# 作業フローガイド

このガイドは、Dr. Aria's Semantic Memory System を使用した作業の開始、中断、再開の基本的な流れを説明します。

## 1. 作業開始 (Start Work)

作業を開始する際は、以下の手順でシステムを起動します。

### 1.1 ターミナルを開く

*   **APIサーバー用ターミナル**: 1つ目のターミナルを開き、`gemini_semantic_memory` ディレクトリに移動します。
*   **CLI用ターミナル**: 2つ目のターミナルを開き、`professor_pi_cli.py` があるディレクトリ（通常は `gemini_semantic_memory` の親ディレクトリ）に移動します。

### 1.2 仮想環境を有効化する

各ターミナルで、以下のコマンドを実行して仮想環境を有効化します。

```bash
# Windowsの場合
.venv\Scripts\activate
# macOS/Linuxの場合
source .venv/bin/activate
```

### 1.3 APIサーバーを起動する

APIサーバー用ターミナルで、以下のコマンドを実行します。

```bash
# gemini_semantic_memory ディレクトリ内で実行
uvicorn main:app --host 0.0.0.0 --port 8000
```
サーバーが起動したら、このターミナルはそのままにしておきます。

### 1.4 CLIを起動する

CLI用ターミナルで、以下のコマンドを実行します。

```bash
# professor_pi_cli.py があるディレクトリで実行
python professor_pi_cli.py
```
CLIが起動し、私（Dr. Aria）との対話を開始できます。

## 2. 作業中断 (Pause Work)

作業を中断する際は、以下の手順でシステムを停止します。

### 2.1 CLIを終了する

CLI用ターミナルで、`You: ` のプロンプトに対して `/exit` と入力し、Enterキーを押します。

```
You: /exit
```
これにより、CLIが終了します。

### 2.2 APIサーバーを停止する

APIサーバー用ターミナルに戻り、キーボードで `Ctrl + C` を押します。
これにより、APIサーバーが停止します。

### 2.3 メモリの永続性について

*   **会話内容**: あなたとの会話内容は、APIサーバーが停止しても、`gemini_semantic_memory/chroma_db` ディレクトリ内のデータベースに永続的に保存されています。
*   **セッションID**: CLIのセッションIDは、`.cli_session_id` ファイルに保存されているため、CLIを終了しても失われません。

## 3. 作業再開 (Resume Work)

作業を再開する際は、「1. 作業開始」の手順を再度実行してください。

*   APIサーバーを起動し、CLIを起動すると、CLIは自動的に前回のセッションIDを読み込み、中断した会話の続きから私との対話を開始できます。
*   過去の会話内容は、APIサーバーがChromaDBから自動的に読み込み、文脈として利用します。
