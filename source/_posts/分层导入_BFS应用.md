---
title: 分层导入：BFS 在分层导入中的实践
main_color: "#16c9f19d"
categories: 业务
tags:
  - 业务
cover: https://free.picui.cn/free/2026/03/28/69c74dc1a2358.webp
---
## 背景与目标

需要实现一个“分层导入”功能：从第三方平台（知识库/文件夹/文件）嵌套导入到本地平台，并完整保留第三方的层次结构与元数据。目标是：
- 保持目录层级一致
- 批量高效入库（减少多次往返与 ID 竞争）
- 与大文件下载/上传解耦，异步推进并可观测进度

## 总体流程（BFS）

整体流程可概括为：
- 用户选择根节点（知识库/文件夹/文件）
- 使用队列按层（BFS）遍历第三方结构，构建本地 Folder/Dataset 实体
- 批量预分配 ID，修正父子引用
- 按层批量入库，注册异步任务
- 通过消息队列触发下载+上传，Redis 实时记录进度

### 流程图

```mermaid
flowchart TD
  A[用户选择 根节点 列表] --> B{节点类型}
  B -- 文件 --> C[构建 Dataset 实体 放入待保存列表]
  B -- 知识库/文件夹 --> D[构建 Folder 实体 入队 level=0]
  D --> E{队列非空?}
  E -- 是 --> F[按层出队 获取子节点]
  F --> G{子节点是文件?}
  G -- 是 --> H[构建 Dataset(挂载父 Folder 临时ID)]
  G -- 否 --> I[构建子 Folder(临时ID) 入队 nextLevel]
  H --> E
  I --> E
  E -- 否 --> J[批量预分配 Folder/Dataset ID]
  J --> K[修正 parentId 和 folderId 引用]
  K --> L[按层批量入库]
  L --> M[发送上传任务到 MQ]
  M --> N[消费者 下载→上传→更新状态→记录/清理进度]
```

## 代码实现

本节包含：
- 入口方法：按层（BFS）组装目录与文件实体，汇总待入库数据
- 批量 ID 预分配：一次性申请 ID 并修正父子引用
- 异步消费者：下载、上传与进度跟踪
- 工具方法：下载并上传（带进度回调）、进度输入流封装

```java
/**
 * 平台导入（不加事务：远程调用 + 构建实体）
 */
public void uploadFilesToPlatform(String graphId, FileUploadRequest fileUploadRequest) {
    List<FileUploadRequestDTO> files = fileUploadRequest.getFileList();
    Long parentId = fileUploadRequest.getFolderId();
    if (parentId == null){
        parentId = folderService.getDefault(graphId).getId();
    }
    DataFromTypeEnum tag = fileUploadRequest.getTag();
    if (CollectionUtils.isEmpty(files)) return;

    List<DatasetEntity> datasetsToSave = new ArrayList<>();
    Map<Integer, List<FolderEntity>> foldersByLevel = new TreeMap<>();

    Deque<FolderLevel> queue = new ArrayDeque<>();

    // 根层
    for (FileUploadRequestDTO file : files) {
        DGPEntityType fileType = file.getType();
        String rootKbId = (fileType == DGPEntityType.KNOWLEDGE_BASE) ? file.getId() : getKbId(file);
        if (fileType == DGPEntityType.FILE) {
            datasetsToSave.add(initDatasetEntity(file, graphId, parentId, tag, rootKbId));
        } else {
            FolderEntity folder = buildFolderEntity(
                    file.getName(), graphId, parentId, tag, file.getId(),
                    fileType == DGPEntityType.KNOWLEDGE_BASE,rootKbId
            );
            foldersByLevel.computeIfAbsent(0, k -> new ArrayList<>()).add(folder);
            queue.offer(new FolderLevel(folder, rootKbId, fileType == DGPEntityType.KNOWLEDGE_BASE, 0));
        }
    }

    // BFS 组装
    while (!queue.isEmpty()) {
        int size = queue.size();
        for (int i = 0; i < size; i++) {
            FolderLevel fl = queue.poll();
            List<DGPShowVo> children = getChildren(fl);
            if (CollectionUtils.isEmpty(children)) continue;

            int nextDepth = fl.depth + 1;
            List<FolderEntity> levelBucket = foldersByLevel.computeIfAbsent(nextDepth, k -> new ArrayList<>());

            for (DGPShowVo child : children) {
                if (Boolean.TRUE.equals(child.getIsFile())) {
                    datasetsToSave.add(buildDatasetEntity(child, graphId, fl.folder.getId(), tag, fl.rootKbId));
                } else {
                    FolderEntity subFolder = buildFolderEntity(
                            child.getName(), graphId, fl.folder.getId(), tag, child.getId(),
                            DGPEntityType.KNOWLEDGE_BASE == child.getType(),
                            fl.rootKbId
                    );
                    levelBucket.add(subFolder);
                    queue.offer(new FolderLevel(subFolder, fl.rootKbId, false, nextDepth));
                }
            }
        }
    }

    // 批量预分配 ID
    allocateIds(foldersByLevel, datasetsToSave);

    // 入库
    datasetDbService.saveToDatabaseByLevel(foldersByLevel, datasetsToSave);
}


/**
 * 批量分配 ID
 */
private void allocateIds(Map<Integer, List<FolderEntity>> foldersByLevel, List<DatasetEntity> datasets) {
    // 扁平化所有 folder
    List<FolderEntity> allFolders = new ArrayList<>();
    foldersByLevel.values().forEach(allFolders::addAll);

    // Folder 批量 ID
    if (!CollectionUtils.isEmpty(allFolders)) {
        Long endFolderId = sequenceMapper.nextFolderIdBatch(allFolders.size());
        Long startFolderId = endFolderId - allFolders.size() + 1;

        Map<Long, Long> tmpIdMap = new HashMap<>();
        for (int i = 0; i < allFolders.size(); i++) {
            FolderEntity f = allFolders.get(i);
            Long tmpKey = f.getId() == null ? System.identityHashCode(f) * 1L : f.getId();
            Long newId = startFolderId + i;
            tmpIdMap.put(tmpKey, newId);
            f.setId(newId);
        }

        // 修正 parentId
        for (FolderEntity f : allFolders) {
            if (f.getParentId() != null) {
                Long fixed = tmpIdMap.get(f.getParentId());
                if (fixed != null) {
                    f.setParentId(fixed);
                }
            }
        }

        // 修正 dataset 的 folderId
        for (DatasetEntity d : datasets) {
            if (d.getFolderId() != null) {
                Long fixed = tmpIdMap.get(d.getFolderId());
                if (fixed != null) {
                    d.setFolderId(fixed);
                }
            }
        }
    }

    // Dataset 批量 ID
    if (!CollectionUtils.isEmpty(datasets)) {
        Long endDatasetId = sequenceMapper.nextDatasetIdBatch(datasets.size());
        Long startDatasetId = endDatasetId - datasets.size() + 1;
        for (int i = 0; i < datasets.size(); i++) {
            datasets.get(i).setId(startDatasetId + i);
        }
    }
}

/** 根层 FILE -> Dataset */
private DatasetEntity initDatasetEntity(FileUploadRequestDTO file, String graphId, Long parentId, DataFromTypeEnum tag, String rootKbId) {
    return DatasetEntity.builder()
            .graphId(graphId)
            .dataName(file.getName())
            .folderId(parentId)
            .importType(tag)
            .dataType(top.usking.sky.knowledge.util.FileUtil.getFileType(file.getName()))
            .uploadStatus(UploadFileEnum.READY.getLabel())
            .dgpFileId(file.getId())
            .kbId(rootKbId)
            .build();
}

/** Folder 子节点/文件 -> Dataset */
private DatasetEntity buildDatasetEntity(DGPShowVo child, String graphId, Long folderId, DataFromTypeEnum tag, String rootKbId) {
    Long size = Optional.ofNullable(child.getRawFileInfo())
            .map(DGPRawFileInfo::getFileSize)
            .map(DGPRawFileSize::getFileSize)
            .map(Long::valueOf)
            .orElse(null);

    return DatasetEntity.builder()
            .graphId(graphId)
            .dataName(child.getName())
            .folderId(folderId)
            .importType(tag)
            .uploadStatus(UploadFileEnum.READY.getLabel())
            .dataType(FileTypeEnum.of(child.getFileType()))
            .dgpFileId(child.getId())
            .kbId(rootKbId)
            .size(size)
            .md5Hash(child.getRawFileInfo().getFileMd5())
            .fileUrl(child.getMinioPath())
            .build();
}

/** 构建 Folder（先用临时 id 占位，后面批量分配新 id） */
private FolderEntity buildFolderEntity(String name, String graphId, Long parentId, DataFromTypeEnum tag,
                                       String thirdPartyFolderId, boolean isKb, String rooKbId) {
    return FolderEntity.builder()
            .id(System.nanoTime()) // 临时 ID，占位用
            .name(name)
            .parentId(parentId)
            .graphId(graphId)
            .fromType(tag)
            .thirdPartyFolderId(thirdPartyFolderId)
            .isKb(isKb)
            .build();
}

/** 取子节点 */
private List<DGPShowVo> getChildren(FolderLevel fl) {
    if (fl.isRootKb) {
        List<DGPFolderEntity> childFolders = dgpService.getZhiHaoFoldersByKbId(fl.rootKbId, false);
        return childFolders.stream()
                .map(f -> DGPShowVo.builder()
                        .id(f.getId())
                        .name(f.getName())
                        .isFile(false)
                        .type(DGPEntityType.FOLDER)
                        .build())
                .toList();
    } else {
        return dgpService.getFoldersAndFilesByKbIdAndFolderId(fl.rootKbId, fl.folder.getThirdPartyFolderId());
    }
}

/** BFS 队列元素 */
private static class FolderLevel {
    FolderEntity folder;
    String rootKbId;
    boolean isRootKb;
    int depth;
    public FolderLevel(FolderEntity folder, String rootKbId, boolean isRootKb, int depth) {
        this.folder = folder;
        this.rootKbId = rootKbId;
        this.isRootKb = isRootKb;
        this.depth = depth;
    }
}

/** 获取 KbId */
private String getKbId(FileUploadRequestDTO file) {
    if (!CollectionUtils.isEmpty(file.getPath())) return file.getPath().get(0).getId();
    return null;
}
```

### 关键点解读（BFS + 批量入库）
- 队列分层遍历：`Deque<FolderLevel>` 保证按层处理，`foldersByLevel` 以深度为 key 聚合同层 `FolderEntity`，便于后续分层入库。
- 根层兼容多类型：既支持直接文件（立即构建 `DatasetEntity`），也支持知识库/文件夹（构建 `FolderEntity` 入队）。
- 子节点装配：文件→`DatasetEntity`；文件夹→`FolderEntity` 并入队，持续 BFS。
- 批量预分配 ID：通过 `sequenceMapper.next*Batch(n)` 获取连续区间，避免并发竞争；用 `tmpIdMap` 修正 `parentId` 与 `folderId` 的临时占位引用。
- 分层入库：`saveToDatabaseByLevel` 可以确保父层先入库（满足外键/层级约束），同时批量写提升吞吐。



### 异步消费者：下载 + 上传 + 进度

```java
@RabbitListener(queues = DirectExchangeConfig.UPLOAD_TASK_QUEUE, ackMode = "MANUAL", concurrency = "3")
public void handleUploadTask(UploadTaskMessage message, Channel channel, Message mqMessage) {
    Long datasetId = message.getDatasetId();
    String fileName = message.getFileName();
    DataFromTypeEnum dataFromTypeEnum = message.getDataFromTypeEnum();
    String fileUrl = message.getFileUrl();
    Long fileSize = message.getFileSize();
    String kbId = message.getKbId();
    String fileId = message.getThirdPartyId();

    String progressKey = "PROGRESS:" + datasetId;

    try {
        // 幂等性检查
        boolean locked = datasetService.updateStatusIfMatch(datasetId, UploadFileEnum.READY, UploadFileEnum.DOWNLOADING);
        if (!locked) {
            log.warn("任务已被处理或正在处理，忽略重复消息 datasetId={}", datasetId);
            channel.basicAck(mqMessage.getMessageProperties().getDeliveryTag(), false);
            return;
        }

        // 下载 + 上传
        redisTemplate.opsForHash().put(progressKey, "percent", "0");
        if (fileUrl ==  null || fileSize == null){
            // 获取文件信息
            DGPFileInfo fileDetail = dgpService.getFileDetail(kbId, fileId);
            fileUrl = fileDetail.getMinioPath();
            fileSize = fileDetail.getRawFileInfo().getFileSize().getFileSize();
        }
        dgpService.downloadAndUpload(fileUrl, fileName, storageProperties.getDefaultBucketName(), fileSize, percent -> {
            redisTemplate.opsForHash().put(progressKey, "percent", String.valueOf(percent));
        });

        // 完成
        datasetService.updateStatus(datasetId, UploadFileEnum.DONE, fileUrl, fileSize);
        redisTemplate.delete(progressKey);

        channel.basicAck(mqMessage.getMessageProperties().getDeliveryTag(), false);
        log.info("文件上传成功: datasetId={}, fileName={}", datasetId, fileName);

    } catch (Exception e) {
        log.error("任务失败 datasetId={}", datasetId, e);
        datasetService.updateStatus(datasetId, UploadFileEnum.ERROR, fileUrl, fileSize);
        redisTemplate.delete(progressKey);
        try {
            channel.basicNack(mqMessage.getMessageProperties().getDeliveryTag(), false, false);
        } catch (IOException ex) {
            throw new RuntimeException(ex);
        }
    }
}

```

说明：
- 幂等与状态机：`updateStatusIfMatch(READY → DOWNLOADING)` 作为“乐观锁”门闩，过滤重复投递。
- 进度跟踪：任务开始在 Redis 写入 `percent=0`，下载/上传过程中持续覆盖更新；完成或失败后清理 Key。
- 信息补全：若消息中无 `fileUrl/fileSize`，先通过远端接口补全，保证后续流程健壮。
- 确认策略：成功 `basicAck`、失败 `basicNack(requeue=false)`，避免死循环；业务错误同时更新数据集状态为 `ERROR`。




### 下载并上传实现（带进度回调）

```java
/**
 * 下载远程文件并上传到存储，支持进度回调
 *
 * @param fileUrl    文件 URL（完整访问地址）
 * @param fileName   目标文件名
 * @param bucketName 存储桶
 * @param progressCallback 进度回调（percent 0~100）
 * @throws IOException 下载或上传异常
 */
public void downloadAndUpload(String fileUrl,
                              String fileName,
                              String bucketName,
                              Long fileSize,
                              Consumer<Double> progressCallback) throws IOException {

    String url = dgpProperties.getUrl() + "/files/download?file_path=" + URLEncoder.encode(fileUrl, StandardCharsets.UTF_8);
    try (HttpResponse response = HttpUtil.createGet(url)
            .header(dgpProperties.getAuthorization(), dgpProperties.getToken())
            .timeout(30000)
            .execute()) {

        if (!response.isOk()) {
            throw new IOException("HTTP 下载失败，状态码: " + response.getStatus());
        }

        try (InputStream rawStream = response.bodyStream()) {
            InputStream inputStream;

            if (fileSize != null && fileSize > 0) {
                // 有文件大小 → 使用进度流
                inputStream = new ProgressInputStream(rawStream, fileSize, progressCallback);
            } else {
                // 没有文件大小 → 不做进度监控
                inputStream = rawStream;
            }

            minioTemplate.putObject(inputStream, bucketName, fileName);

            // 上传完成后，如果需要回调 100%
            if (progressCallback != null) {
                progressCallback.accept(100.0);
            }
        }
    }
}

```

说明：
- 直连下载：拼接受控下载 URL，携带鉴权头；统一 30s 连接/首包超时。
- 进度包装：若已知文件大小，则用 `ProgressInputStream` 计算百分比并回调；未知大小则直接透传。
- 上传落地：通过 `minioTemplate.putObject` 写入目标桶；结束后兜底回调 100%。


### 进度流封装：`ProgressInputStream`

```java
public class ProgressInputStream extends FilterInputStream {
    private final long totalBytes;
    private final Consumer<Double> progressCallback;
    private long bytesRead = 0;
    private long lastUpdateTime = System.currentTimeMillis();

    public ProgressInputStream(InputStream in, long totalBytes, Consumer<Double> progressCallback) {
        super(in);
        this.totalBytes = totalBytes;
        this.progressCallback = progressCallback;
    }

    @Override
    public int read() throws IOException {
        int b = super.read();
        if (b != -1) updateProgress(1);
        return b;
    }

    @Override
    public int read(byte[] b, int off, int len) throws IOException {
        int n = super.read(b, off, len);
        if (n > 0) updateProgress(n);
        return n;
    }

    private void updateProgress(int n) {
        bytesRead += n;
        long now = System.currentTimeMillis();
        if (totalBytes > 0 && (now - lastUpdateTime > 200 || bytesRead == totalBytes)) {
            double percent = bytesRead * 100.0 / totalBytes;
            progressCallback.accept(percent);
            lastUpdateTime = now;
        }
    }
}
```

说明：
- 轻量封装：覆盖 `read`/`read(byte[],...)`，累计字节数。
- 节流回调：每 ≥200ms 或读满时触发一次，避免频繁调用造成抖动与负载。
- 精度足够：以 `totalBytes` 计算百分比，满足前端进度条展示需求。

## 设计思想与取舍
- 解耦与弹性：导入建模与大文件传输彻底解耦，写库后通过 MQ 异步推进，提升可用性与可观测性。
- 幂等与一致性：状态跳变采用 CAS 语义（READY→DOWNLOADING→DONE/ERROR），防止重复消费与乱序更新。
- 批量化：ID 批量分配与分层批量入库减少往返，提升吞吐并弱化热点竞争。
- 资源控制：下载流式转发至对象存储，避免本地落盘与过度内存占用。
- 有损重试的权衡：消费失败 `nack(requeue=false)` 交由死信/报警处理，避免毒消息无限重试。

## 风险与改进建议
- 任务可恢复性：引入任务表记录状态与失败原因，配合补偿任务（重试/续传）。
- 大文件断点续传：对接对象存储的分片/断点能力，失败可从最近分片继续。
- 目录深度与规模：限制最大深度与节点总量，防止恶意/异常数据导致长时间处理。
- 速率与并发：下载/上传并发数配置化；进度回调节流窗口可调。
- 安全性：下载 URL 采用临时签名；最小权限的对象存储凭证；敏感日志脱敏。
- 可观测：增加 Prometheus 指标（队列滞留、成功率、P95/P99 时延、带宽利用）。

## 总结
- 使用 BFS 保障“按层构建、按层入库”，结合批量 ID 预分配，实现高效且结构稳定的导入。
- 通过 MQ 解耦长耗时的下载/上传，并以 Redis 实时记录进度，用户可见性与系统鲁棒性兼顾。
- 设计在幂等、批量化、资源节制上做出权衡，后续可围绕可恢复性与可观测性持续优化。


