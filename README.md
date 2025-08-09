# Dr. Aria's Semantic Memory System

## プロジェクト概要

このプロジェクトは、Geminiモデルにセッションをまたいだ永続的な記憶能力を付与するためのシステムです。会話の内容をベクトル化し、ローカルのベクトルデータベース（ChromaDB）に保存することで、AIが過去の対話の文脈を「記憶」し、それを踏まえた応答を生成できるようになります。

## 主要コンポーネント

- **FastAPI**: APIサーバーとして機能し、CLIや他のアプリケーションからのリクエストを受け付けます。
- **ChromaDB**: ベクトルデータベースとして、会話の埋め込みベクトルとメタデータを永続的に保存します。
- **Sentence-Transformers**: テキストを数値ベクトル（埋め込み）に変換するために使用します。
- **Google Generative AI**: Geminiモデルとの対話を行います。

## セットアップ

### 1. プロジェクトのクローン

```bash
git clone <リポジトリのURL>
cd gemini_semantic_memory
```

### 2. 仮想環境の作成と有効化

```bash
python -m venv .venv
# Windowsの場合
.venv\Scripts\activate
# macOS/Linuxの場合
source .venv/bin/activate
```

### 3. 依存関係のインストール

以下のコマンドで必要なライブラリをインストールします。

```bash
pip install numpy pandas spacy tiktoken chromadb sentence-transformers==2.7.0 google-generativeai==0.8.0 fastapi==0.110.0 uvicorn==0.29.0 pydantic==2.7.0 python-dotenv==1.0.0 plotly==5.20.0
# spacyの言語モデルをダウンロード
python -m spacy download ja_core_news_sm
```

### 4. 環境変数の設定

プロジェクトルートにある`.env`ファイルを編集し、`GEMINI_API_KEY`を設定してください。

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

## 実行方法

### 1. APIサーバーの起動

新しいターミナルを開き、`gemini_semantic_memory`ディレクトリに移動し、仮想環境を有効化した状態で以下のコマンドを実行します。このサーバーはバックグラウンドで起動し続けます。

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

サーバーが起動したら、ブラウザで `http://127.0.0.1:8000/docs` にアクセスすると、APIのドキュメントとテストインターフェースが表示されます。

### 2. CLIの実行

別のターミナルを開き、`gemini_semantic_memory`ディレクトリの親ディレクトリ（プロジェクトのルート）に移動し、仮想環境を有効化した状態で以下のコマンドを実行します。

```bash
python professor_pi_cli.py
```

CLIを起動すると、APIサーバーと連携して会話履歴を記憶・活用するようになります。CLIを再起動しても、前回の会話セッションが自動的に継続されます。

## 重要な概念

- **セッション**: 会話のまとまりを識別するための単位です。CLIを再起動しても、同じセッションIDが使用され、会話が継続されます。
- **記憶の永続化**: 会話内容はローカルのChromaDBに保存されるため、PCの電源を切っても記憶が失われることはありません。
- **セマンティック検索**: ユーザーの質問と関連性の高い過去の記憶を、意味に基づいて検索し、Geminiモデルに提供します。

## 開発者向け

### APIエンドポイント

- `POST /chat`: アシスタントとの会話を開始/継続します。`session_id`を省略すると新規セッションが自動作成されます。
- `POST /sessions/`: 新しい会話セッションを手動で作成します。
- `GET /sessions/`: 既存の会話セッションのリストを取得します。

### プロジェクト構造

```
gemini_semantic_memory/
├── .env
├── requirements.txt
├── main.py
├── professor_pi_cli.py
├── README.md
├── config/
│   └── settings.py
├── core/
│   ├── memory_manager.py
│   ├── embedding_service.py
│   └── gemini_client.py
├── models/
│   ├── conversation.py
│   └── memory_record.py
├── data/
│   ├── personas/
│   └── cache/
└── tests/
    ├── test_memory.py
    ├── test_embedding.py
    └── test_retrieval.py
```
