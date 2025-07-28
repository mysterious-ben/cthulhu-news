# Cthulhu News Architecture

```mermaid
graph TB
    %% External Services
    GNews[GNews API<br/>Real News Source]
    Media[News Websites]
    GPT4[OpenAI GPT-4<br/>Story Generation]
    DALLE3[OpenAI DALL-E 3<br/>Image Generation]
    
    %% User Interface
    Users[Browsers & Readers</br>stranger.news]
    
    %% Web Layer
    WebPage[cthulhu-webapp<br/>HTML + JS<br/>FastAPI Server<br/>:8000]
    
    %% Processing Layer  
    WebETL[cthulhu-etl<br/>Text Generation<br/>ETL Pipeline]
    DBETL[db-etl<br/>News Collection<br/>ETL Pipeline]
    
    %% Orchestration
    Prefect[Prefect<br/>Workflow Orchestration<br/>Server + Worker<br/>:4200]
    PrefectUI[Prefect UI<br/>:4200]
    
    %% Data Layer
    MongoDB[(MongoDB<br/>Raw News Articles<br/>:27017)]
    PostgreSQL[(PostgreSQL + pgvector<br/>Processed Stories<br/>:5432)]
    
    %% Management Tools
    MongoExpress[Mongo Express UI<br/>:8081]
    
    %% Data Flow
    GNews -->|Fetch News Metadata| DBETL
    Media -->|Upload News Articles| DBETL
    DBETL -->|Store Articles| MongoDB
    GPT4 -->|Tags & Summary| DBETL
    
    MongoDB -->|Read Articles| WebETL
    GPT4 -->|Lovecraftian Stories| WebETL
    DALLE3 -->|Horror Images| WebETL
    WebETL -->|Store Processed| PostgreSQL
    
    PostgreSQL -->|Serve Stories| WebPage
    WebPage -->|External Web| Users
    Users -->|Upvotes & Comments| WebETL
    
    %% Orchestration Flow
    Prefect -->|Schedule & Execute| DBETL
    Prefect -->|Schedule & Execute| WebETL
    Prefect --> PrefectUI
    
    %% Management
    MongoDB --> MongoExpress
    
    %% Styling
    classDef external fill:#e1f5fe,stroke:#01579b,stroke-width:3px,color:#000000
    classDef web fill:#f3e5f5,stroke:#4a148c,stroke-width:3px,color:#000000
    classDef processing fill:#fff3e0,stroke:#e65100,stroke-width:3px,color:#000000
    classDef data fill:#e8f5e8,stroke:#1b5e20,stroke-width:3px,color:#000000
    classDef orchestration fill:#fce4ec,stroke:#880e4f,stroke-width:3px,color:#000000
    
    class GNews,Media,GPT4,DALLE3,Users external
    class WebPage web
    class WebETL,DBETL processing
    class MongoDB,PostgreSQL data
    class Prefect orchestration
```

## Architecture Overview

### 3-Tier Microservices Architecture

**Presentation Tier**
- `web-page`: FastAPI web server serving the horror news interface
- Jinja2 templates with custom horror-themed styling

**Business Logic Tier**  
- `web-etl`: Transforms news articles into Lovecraftian stories using OpenAI
- `db-etl`: Collects and preprocesses news articles from GNews API
- Prefect orchestrates and schedules ETL workflows

**Data Tier**
- MongoDB: Stores raw news articles and metadata
- PostgreSQL + pgvector: Stores processed stories with vector embeddings
- mongo-express: Database administration interface

### Data Flow

1. **Collection**: `db-etl` fetches news from GNews API → stores in MongoDB
2. **Processing**: `web-etl` reads articles → generates Cthulhu stories via OpenAI → stores in PostgreSQL  
3. **Presentation**: `web-page` serves processed stories through horror-themed web interface
4. **Orchestration**: Prefect manages workflow scheduling and execution

### Key Technologies
- **Containerization**: Docker Compose orchestrates all services
- **AI Integration**: OpenAI GPT-4 for story generation, DALL-E 3 for images
- **Vector Search**: pgvector enables semantic story similarity
- **Workflow Management**: Prefect handles ETL scheduling and monitoring

## LLM Workflow Pipeline (web/llm_cthulhu_new.py)

```mermaid
flowchart TD
    %% Input
    NewsArticle[News Article<br/>Title, Summary, URL]
    ExistingStories[Existing Cthulhu Stories<br/>For Context & Continuity]
    
    %% Scene Generation Pipeline
    SceneParams[Generate Scene Parameters<br/>- Protagonist: Cultists vs Detectives<br/>- Characters: 1-2 random selection<br/>- Scene Type: 8 types available<br/>- Narrator: Witness archetype<br/>- Protocol Step: Based on counters<br/>- Outcome: Success/Mixed/Failure]
    
    StoryPrompt[Create Story Prompt<br/>- Character backgrounds<br/>- Current story context<br/>- News integration<br/>- JSON response format]
    
    GPTWriter[OpenAI GPT-4<br/>Writer Model<br/>generate_cthulhu_news]
    
    SceneGeneration[Scene Generation<br/>- scene_title<br/>- scene_text <br/>- Lovecraftian narrative]
    
    SummaryPrompt[Create Summary Prompt<br/>- Story continuity<br/>- Character development<br/>- Plot progression]
    
    GPTSummarizer[OpenAI GPT-4<br/>Summarizer Model<br/>Story Coherence]
    
    StoryUpdate[Update Story Summary<br/>- Maintain continuity<br/>- Track character arcs<br/>- Update win counters]
    
    %% Image Generation Pipeline
    ImagePrompt[Create Image Prompt<br/>- News summary context<br/>- Scene description<br/>- Style: Dark retro surrealism]
    
    DALLE3[OpenAI DALL-E 3<br/>Image Generation<br/>1024x1024 PNG]
    
    ImageProcess[Process & Store Image<br/>- Base64 decode<br/>- File naming<br/>- Metadata storage]
    
    %% Character System
    Cultists[Cultists Group<br/>Goal: Summon Cthulhu<br/>- The Bishop<br/>- The Technomancer<br/>- The Oracle<br/>- The Visionary]
    
    Detectives[Detectives Group<br/>Goal: Stop the cult<br/>- The Scribe<br/>- The Warden<br/>- The Seeker<br/>- The Enchantress]
    
    Witnesses[Witness Narrators<br/>- The Archivist: formal<br/>- The Coffee Seer: casual]
    
    %% Protocol System
    CultProtocol[Cultist Protocol<br/>10 Steps → Final Conjuration<br/>Scholar → Network → Relics → Victory]
    
    DetectiveProtocol[Detective Protocol<br/>10 Steps → Final Stand<br/>Assemble → Expose → Seal → Victory]
    
    %% Output
    CompleteStory[Complete Cthulhu Story<br/>- Scene with horror narrative<br/>- AI-generated image<br/>- Updated story context<br/>- Character progression]
    
    %% Data Flow
    NewsArticle --> SceneParams
    ExistingStories --> SceneParams
    SceneParams --> StoryPrompt
    StoryPrompt --> GPTWriter
    GPTWriter --> SceneGeneration
    SceneGeneration --> SummaryPrompt
    SummaryPrompt --> GPTSummarizer
    GPTSummarizer --> StoryUpdate
    
    %% Image Flow
    NewsArticle --> ImagePrompt
    SceneGeneration --> ImagePrompt
    ImagePrompt --> DALLE3
    DALLE3 --> ImageProcess
    
    %% Character Selection
    Cultists -.-> SceneParams
    Detectives -.-> SceneParams
    Witnesses -.-> SceneParams
    
    %% Protocol Flow
    CultProtocol -.-> SceneParams
    DetectiveProtocol -.-> SceneParams
    
    %% Final Assembly
    StoryUpdate --> CompleteStory
    ImageProcess --> CompleteStory
    
    %% Styling
    classDef input fill:#e8f5e8,stroke:#1b5e20,stroke-width:3px,color:#000000
    classDef process fill:#fff3e0,stroke:#e65100,stroke-width:3px,color:#000000
    classDef ai fill:#e1f5fe,stroke:#01579b,stroke-width:3px,color:#000000
    classDef character fill:#f3e5f5,stroke:#4a148c,stroke-width:3px,color:#000000
    classDef protocol fill:#fce4ec,stroke:#880e4f,stroke-width:3px,color:#000000
    classDef output fill:#f3e5ab,stroke:#f57f17,stroke-width:3px,color:#000000
    
    class NewsArticle,ExistingStories input
    class SceneParams,StoryPrompt,SceneGeneration,SummaryPrompt,StoryUpdate,ImagePrompt,ImageProcess process
    class GPTWriter,GPTSummarizer,DALLE3 ai
    class Cultists,Detectives,Witnesses character
    class CultProtocol,DetectiveProtocol protocol
    class CompleteStory output
```

### LLM Workflow Features

**Multi-Stage Story Generation**
- **Character-Driven**: Alternates between Cultists vs Detectives protagonists
- **Structured Narrative**: 8 scene types (Exposition, Dialogue, Investigation, etc.)
- **Win Counter System**: Progressive 10-step protocols for each faction
- **Witness Narration**: Two distinct narrative voices (Archivist, Coffee Seer)

**Advanced Prompt Engineering**
- **Role-Based Prompting**: Distinct system roles for different AI tasks
- **Context Building**: Dynamic story history and character integration
- **JSON Response Format**: Structured output with field validation
- **Sample Templates**: Consistent Lovecraftian style examples

**Integrated Image Generation**
- **Contextual Prompts**: Combines news content with scene descriptions
- **Consistent Style**: "Dark retro surrealism" aesthetic
- **Metadata Tracking**: Comprehensive image generation logging
- **File Management**: Organized storage with sanitized naming

**Story Continuity System**
- **Ongoing Summary**: Maintained across all scenes for coherence
- **Character Development**: Consistent personality and background tracking
- **Plot Progression**: Win counters determine available protocol actions
- **Victory Conditions**: Story concludes when faction achieves final protocol