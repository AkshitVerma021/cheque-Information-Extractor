# Cheque Information Extractor - Flowcharts

This document contains flowcharts that illustrate the architecture and workflow of the Cheque Information Extractor application.

## Application Workflow

```mermaid
flowchart TD
    start[User opens application] --> upload[User uploads cheque images]
    upload --> validation{Validate images}
    
    validation -->|Valid| processing[Process images]
    validation -->|Invalid| error[Display error message]
    error --> upload
    
    processing --> extraction[Extract data with Claude 3 Haiku]
    extraction --> sonnet[Cross-validate with Claude 3 Sonnet]
    
    sonnet --> ruleValidation[Apply banking rule validation]
    ruleValidation --> confidence[Calculate confidence score]
    
    confidence --> signature[Extract signature region]
    signature --> s3Storage[Store images in S3]
    
    s3Storage --> display[Display results to user]
    display --> select[User selects cheque from dropdown]
    
    select --> viewDetails[View extraction details]
    viewDetails --> export[Export results to Excel]
    
    export --> s3Excel[Store Excel in S3]
    s3Excel --> download[User downloads Excel]
    
    viewDetails --> clear[Clear data and start again]
    clear --> upload
```

## System Architecture

```mermaid
flowchart LR
    subgraph Frontend["Frontend (Streamlit)"]
        ui[UI Components]
        session[Session Manager]
        display[Display Module]
    end
    
    subgraph Processing["Processing Layer"]
        processor[Cheque Processor]
        validator[Cheque Validator]
        export[Export Utilities]
    end
    
    subgraph Services["External Services"]
        ai[AI Service]
        s3[S3 Service]
    end
    
    subgraph Models["Data Models"]
        chequeData[Cheque Data]
        validationResult[Validation Result]
        processedCheque[Processed Cheque]
    end
    
    subgraph External["External Systems"]
        awsBedrock[AWS Bedrock]
        awsS3[AWS S3]
    end
    
    ui --> session
    ui --> display
    display --> processor
    processor --> validator
    processor --> ai
    processor --> s3
    processor --> export
    
    ai --> awsBedrock
    s3 --> awsS3
    
    processor --> Models
    validator --> Models
    
    classDef frontend fill:#D6EAF8,stroke:#2E86C1,stroke-width:2px
    classDef processing fill:#D5F5E3,stroke:#27AE60,stroke-width:2px
    classDef services fill:#FCF3CF,stroke:#F1C40F,stroke-width:2px
    classDef models fill:#FADBD8,stroke:#E74C3C,stroke-width:2px
    classDef external fill:#E5E8E8,stroke:#566573,stroke-width:2px
    
    class Frontend frontend
    class Processing processing
    class Services services
    class Models models
    class External external
```

## Data Processing Flow

```mermaid
sequenceDiagram
    participant User
    participant UI as UI (Streamlit)
    participant Processor as Cheque Processor
    participant AI as AI Service
    participant Validator as Cheque Validator
    participant S3 as S3 Service
    participant Bedrock as AWS Bedrock
    participant S3Bucket as AWS S3 Bucket

    User->>UI: Upload cheque image(s)
    UI->>Processor: Process images
    
    loop For each image
        Processor->>AI: Process image
        AI->>Bedrock: Validate image (Haiku)
        Bedrock-->>AI: Validation result
        
        alt Valid cheque
            AI->>Bedrock: Extract data (Haiku)
            Bedrock-->>AI: Haiku extraction result
            AI->>Bedrock: Extract data (Sonnet)
            Bedrock-->>AI: Sonnet extraction result
            AI-->>Processor: Extraction results
            
            Processor->>Validator: Validate data
            Validator-->>Processor: Validation results
            
            Processor->>Validator: Cross-validate results
            Validator-->>Processor: Discrepancies & confidence
            
            Processor->>S3: Upload original image
            S3->>S3Bucket: Store image
            S3Bucket-->>S3: S3 URL
            
            Processor->>S3: Extract & upload signature
            S3->>S3Bucket: Store signature
            S3Bucket-->>S3: Signature URL
            
            S3-->>Processor: S3 URLs
        else Invalid cheque
            AI-->>Processor: Invalid image error
        end
    end
    
    Processor-->>UI: Processed cheques
    UI->>User: Display results
    
    User->>UI: Select cheque
    UI->>User: Display details
    
    User->>UI: Request Excel export
    UI->>Processor: Generate Excel
    Processor->>S3: Upload Excel
    S3->>S3Bucket: Store Excel
    S3Bucket-->>S3: Excel URL
    S3-->>Processor: Excel URL
    Processor-->>UI: Excel bytes & URL
    UI->>User: Download Excel
```

## Validation Process

```mermaid
flowchart TD
    start[Start Validation] --> haiku[Extract with Claude 3 Haiku]
    haiku --> sonnet[Extract with Claude 3 Sonnet]
    
    sonnet --> crossValidate[Cross-validate Results]
    crossValidate --> discrepancies{Any Discrepancies?}
    
    discrepancies -->|Yes| calculateScore1[Lower confidence score]
    discrepancies -->|No| calculateScore2[Higher confidence score]
    
    calculateScore1 --> ruleValidation[Apply Rule-based Validation]
    calculateScore2 --> ruleValidation
    
    ruleValidation --> bank[Validate Bank Name]
    bank --> account[Validate Account Number]
    account --> ifsc[Validate IFSC Code]
    ifsc --> date[Validate Date Format]
    date --> amount[Validate Amount]
    
    amount --> combineScores[Combine Cross-validation & Rule-based Scores]
    combineScores --> finalScore[Final Confidence Score]
    
    finalScore --> thresholds{Confidence Level}
    thresholds -->|90-100%| high[High Confidence]
    thresholds -->|70-89%| medium[Medium Confidence]
    thresholds -->|<70%| low[Low Confidence]
    
    high --> display[Display in UI]
    medium --> display
    low --> display
```

## S3 Storage Structure

```mermaid
flowchart TD
    s3[AWS S3 Bucket] --> processed[/processed/ folder]
    s3 --> signatures[/signatures/ folder]
    s3 --> reports[/excel_reports/ folder]
    
    processed --> cheque1[cheque_20240529_123456_123456789.jpg]
    processed --> cheque2[cheque_20240529_123457_987654321.jpg]
    processed --> chequeN[cheque_*.jpg]
    
    signatures --> sig1[signature_20240529_123456_123456789.jpg]
    signatures --> sig2[signature_20240529_123457_987654321.jpg]
    signatures --> sigN[signature_*.jpg]
    
    reports --> excel1[cheque_report_20240529_123456.xlsx]
    reports --> excel2[cheque_report_20240529_145623.xlsx]
    reports --> excelN[cheque_report_*.xlsx]
    
    classDef folder fill:#f9f9f9,stroke:#333,stroke-width:2px
    classDef file fill:#e8f4f8,stroke:#333,stroke-width:1px
    
    class s3,processed,signatures,reports folder
    class cheque1,cheque2,chequeN,sig1,sig2,sigN,excel1,excel2,excelN file
```

## Component Interaction

```mermaid
stateDiagram-v2
    [*] --> StreamlitUI: User Access
    StreamlitUI --> FileUpload: Upload Files
    
    state FileUpload {
        [*] --> CheckValidCheque
        CheckValidCheque --> ImageValidation: Valid
        CheckValidCheque --> Error: Invalid
        Error --> [*]
    }
    
    FileUpload --> ProcessorWorkflow: Process Images
    
    state ProcessorWorkflow {
        [*] --> AIService
        
        state AIService {
            [*] --> HaikuExtraction
            HaikuExtraction --> SonnetExtraction
            SonnetExtraction --> [*]
        }
        
        AIService --> ValidationService
        
        state ValidationService {
            [*] --> FieldValidation
            FieldValidation --> CrossValidation
            CrossValidation --> ConfidenceCalculation
            ConfidenceCalculation --> [*]
        }
        
        ValidationService --> S3Service
        
        state S3Service {
            [*] --> SaveChequeImage
            SaveChequeImage --> ExtractSignature
            ExtractSignature --> SaveSignature
            SaveSignature --> [*]
        }
    }
    
    ProcessorWorkflow --> ResultsDisplay: Processed Results
    
    state ResultsDisplay {
        [*] --> ChequeSelector
        ChequeSelector --> DetailedView
        DetailedView --> ExportData
        ExportData --> [*]
    }
    
    ResultsDisplay --> SessionClear: Clear Session
    SessionClear --> FileUpload: Start Again
```

## Error Handling Flow

```mermaid
flowchart TD
    start[User Action] --> tryBlock[Try Block]
    
    tryBlock --> imageValid{Valid Image?}
    imageValid -->|Yes| formatValid{Valid Format?}
    imageValid -->|No| imageError[Image Error]
    
    formatValid -->|Yes| awsConnection{AWS Connected?}
    formatValid -->|No| formatError[Format Error]
    
    awsConnection -->|Yes| processing[Process Data]
    awsConnection -->|No| connectionError[Connection Error]
    
    processing --> s3Upload{S3 Upload OK?}
    s3Upload -->|Yes| complete[Complete Processing]
    s3Upload -->|No| uploadError[Upload Error]
    
    imageError --> errorHandler[Error Handler]
    formatError --> errorHandler
    connectionError --> errorHandler
    uploadError --> errorHandler
    
    errorHandler --> displayError[Display Error Message]
    displayError --> retry{Retry?}
    
    retry -->|Yes| start
    retry -->|No| finished[End Process]
    
    complete --> results[Return Results]
``` 