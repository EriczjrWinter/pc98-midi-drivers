# EMD-98（ayayo2_98）——独立驱动，不属于风雅

## 包

```text
ayayo2_98
[PC-9801] はっちゃけあやよさんII 「いけないホリディ」 AYAYO'S LOVE AFFAIR
```

HOOT shell：

```text
FMD -M6 -N0
EMD_98
```

包内可执行：

```text
FMD.EXE      7051
EMD_98.COM
```

## 源文件

```text
AYA1.EMI
AYA2.EMI
AYA3.EMI
AYA4.EMI
AYAM.EMI
```

5 首，`.EMI` 头：

```text
45 4D 00 06 ...   ("EM")
```

## 为什么不属于 FMD

- 直接让 FMD.EXE 7051 + ` -M6 -N0` 跑 `.EMI` 会 `UC_ERR_EXCEPTION`；
- `.EMI` 不是 FMD 的 4 字节记录流；
- 真正入口是 `EMD_98.COM`，需要用它的读文件/命令流分析。

## 当前状态

```text
未导出 / 新驱动未开始
```

下一步：

1. 追 `EMD_98.COM` 的入口、INT 21 文件读取、端口写入；
2. 确认 `.EMI` 头部各字段；
3. 再决定是否写 EMI 解析器。

FMD 文档不再把 ayayo2 列为“风雅未完成”。
