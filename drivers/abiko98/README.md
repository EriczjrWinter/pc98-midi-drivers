# ABIKO-98（sematte_98）——独立驱动，不属于风雅

## 包

```text
sematte_98
[PC-9801] せまってみたい
```

HOOT shell：

```text
FMD
ABIKO_98
```

包内可执行：

```text
FMD.EXE      22392
ABIKO_98.COM
```

## 源文件

```text
RIKA01.MUS / RIKA01.ONS
...
RIKA06.MUS / RIKA06.ONS
```

共 6 组：

- `.MUS`：2 字节左右的参数流，`FA/FB/FC/FD/FE/FF` 命令密集；
- `.ONS`：固定 256 字节的元数据/控制块；
- 实际播放由 `ABIKO_98.COM` 壳负责。

## 为什么不属于 FMD

- `.MUS/.ONS` 不是 FMD 的 4 字节记录流；
- 包内真正入口是 `ABIKO_98.COM`；
- 直接按 FMD profile 批跑不会得到正确结果。

## 当前状态

```text
未导出 / 新驱动未开始
```

下一步：

1. 追 `ABIKO_98.COM` 的入口与文件读取；
2. 解析 `.MUS` 命令流和 `.ONS` 256 字节块的关系；
3. 再决定是否写独立 MUS/ONS 解析器。

FMD 文档不再把 sematte 列为“风雅未完成”。
