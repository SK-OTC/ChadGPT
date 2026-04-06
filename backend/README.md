# Chad Information RAG GPT Wrapper

A specialized AI assistant that **only** answers questions about the Republic of Chad using RAG (Retrieval Augmented Generation). This example demonstrates how to wrap a general-purpose GPT model around a specific subject with a custom knowledge base.

## 🎯 What This Does

- **Subject-Specific**: Only answers questions about Chad (the African country)
- **RAG Implementation**: Uses a curated knowledge base to provide accurate, grounded answers
- **Input Validation**: Automatically detects and rejects off-topic questions
- **Free Options**: Works without an API key (knowledge base only) or with Claude API for enhanced responses

## 📁 Files Included

1. **chad-rag-gpt.html** - Complete frontend implementation (HTML + JavaScript)
2. **chad_rag_backend.py** - Python Flask backend with API
3. **README.md** - This documentation

## 🚀 Quick Start

### Option 1: HTML Version (Easiest)

1. Open `chad-rag-gpt.html` in a web browser
2. Start asking questions about Chad!

**Note**: This version includes a fallback mode if the API fails - it will use the knowledge base directly (100% free).

### Option 2: Python Backend

```bash
# Install dependencies
pip install flask anthropic flask-cors --break-system-packages

# Run the server
python chad_rag_backend.py

# Open browser to http://localhost:5000
```

## 💡 How It Works

### 1. Knowledge Base Structure

The wrapper contains 8 curated sections about Chad:

```javascript
CHAD_KNOWLEDGE_BASE = {
    geography: { content: "...", keywords: [...] },
    population: { content: "...", keywords: [...] },
    economy: { content: "...", keywords: [...] },
    history: { content: "...", keywords: [...] },
    tourism: { content: "...", keywords: [...] },
    culture: { content: "...", keywords: [...] },
    wildlife: { content: "...", keywords: [...] },
    challenges: { content: "...", keywords: [...] }
}
```

### 2. RAG Process Flow

```
User Question
    ↓
Is it about Chad? → NO → "I only answer questions about Chad"
    ↓ YES
Search Knowledge Base
    ↓
Find 2 Most Relevant Sections
    ↓
Build Context Prompt
    ↓
Send to Claude API (or use fallback)
    ↓
Return Answer + Sources
```

### 3. Semantic Search

The system ranks knowledge sections by:
- **Keyword matches** (10 points each)
- **Content matches** (3 points per word)
- Returns top 2 most relevant sections

### 4. System Prompt

```javascript
systemPrompt = `You are a specialized information assistant focused 
exclusively on the Republic of Chad in Africa.

Rules:
- ONLY answer questions about Chad
- Base answers on provided context
- Be informative but concise
- Cite specific facts when available
- If asked about other topics, redirect to Chad

Tone: Informative, engaging, educational`
```

## 📊 Example Queries

### ✅ Good Questions (Will Answer)

- "What are the main tourist attractions in Chad?"
- "Tell me about Lake Chad"
- "What languages are spoken in Chad?"
- "What is the economy based on?"
- "How large is Chad?"
- "Tell me about Zakouma National Park"

### ❌ Rejected Questions

- "What's the capital of France?" → Off-topic
- "How do I make pasta?" → Not about Chad
- "Tell me about Nigeria" → Different country

## 🔧 Customization Guide

### To Adapt This for Another Subject:

1. **Replace Knowledge Base**
```javascript
const YOUR_SUBJECT_KB = {
    category1: {
        content: "Your curated information here...",
        keywords: ['keyword1', 'keyword2', 'keyword3']
    },
    // Add more categories
}
```

2. **Update Validation Function**
```javascript
function isAboutYourSubject(query) {
    const keywords = ['your', 'subject', 'keywords'];
    return keywords.some(kw => query.toLowerCase().includes(kw));
}
```

3. **Customize System Prompt**
```javascript
const systemPrompt = `You are an expert on [YOUR SUBJECT].

Your expertise includes:
- Topic 1
- Topic 2
- Topic 3

Rules:
- ONLY answer questions about [YOUR SUBJECT]
- Base answers on provided context
- [Add your specific rules]
`;
```

4. **Update UI/Branding**
- Change colors in CSS
- Update header text
- Modify example questions

## 🎨 UI Features

- **Chat Interface**: Clean, modern messaging UI
- **Color Scheme**: Chad flag colors (Blue, Yellow, Red)
- **Loading Animation**: Elegant dots while processing
- **Source Tags**: Shows which knowledge sections were used
- **Example Questions**: Quick-start buttons for common queries
- **Mobile Responsive**: Works on all screen sizes

## 🔑 API Integration

### With Claude API (Better Responses)

```javascript
// In HTML version, API is called automatically
// Just make sure your browser can access api.anthropic.com

const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 1000,
        system: systemPrompt + "\n\n" + context,
        messages: [{ role: 'user', content: userQuestion }]
    })
});
```

### Python Backend API

```python
# Free mode (no API key)
POST http://localhost:5000/api/ask
{
    "question": "What is Lake Chad?"
}

# With API (better responses)
POST http://localhost:5000/api/ask
{
    "question": "What is Lake Chad?",
    "api_key": "your-anthropic-api-key"
}
```

## 💰 Cost Considerations

### Free Option
- Uses knowledge base only
- No API calls
- Instant responses
- Good for basic information retrieval

### Claude API Option
- Better natural language understanding
- More conversational responses
- Better at complex questions
- **Cost**: ~$0.003 per request (using Claude Sonnet 4)

## 🛡️ Safety Features

1. **Topic Validation**: Rejects off-topic questions
2. **Context Grounding**: Only uses provided knowledge
3. **Graceful Fallback**: Works without API if needed
4. **Error Handling**: Catches and handles API failures

## 📚 Knowledge Base Content

The current knowledge base includes verified information about:

- **Geography**: Size, location, borders, climate zones, Lake Chad
- **Population**: Demographics, ethnic diversity, languages (200+ groups, 120+ languages)
- **Economy**: Oil industry, agriculture, cotton, poverty statistics
- **History**: From ancient kingdoms to 2024 elections
- **Tourism**: Zakouma Park, Ennedi Plateau, Tibesti Mountains, Ounianga Lakes
- **Culture**: Food (millet-based), sports (soccer), 200+ ethnic groups
- **Wildlife**: Elephants, lions, crocodiles, 373+ bird species
- **Challenges**: Poverty, health issues, environmental concerns

## 🔄 Updating the Knowledge Base

To add new information:

1. Research and verify facts
2. Add to appropriate category or create new category
3. Update keywords list
4. Test with relevant questions

```javascript
newCategory: {
    content: `Your new verified information here.
    
    Use clear paragraphs and specific facts.
    
    Include statistics and dates when available.`,
    
    keywords: ['relevant', 'search', 'terms']
}
```

## 🚀 Deployment Options

### GitHub Pages (Free)
1. Upload `chad-rag-gpt.html`
2. Enable GitHub Pages
3. Access via `https://yourusername.github.io/chad-rag-gpt.html`

### Netlify (Free)
1. Drag and drop HTML file
2. Get instant URL
3. No configuration needed

### Python Backend (Heroku, Railway, etc.)
1. Deploy `chad_rag_backend.py`
2. Set environment variables
3. Connect frontend to backend URL

## 🎓 Learning Outcomes

This example teaches:

1. **RAG Fundamentals**: How to augment AI with external knowledge
2. **Semantic Search**: Simple keyword-based retrieval
3. **Prompt Engineering**: Constraining AI to specific domains
4. **Input Validation**: Filtering off-topic queries
5. **Graceful Degradation**: Fallback when APIs fail
6. **Full-Stack AI**: Frontend + Backend + AI integration

## 🔍 Limitations

1. **Knowledge Cutoff**: Based on February 2026 research
2. **Static KB**: Doesn't update automatically
3. **Simple Search**: Basic keyword matching (not vector embeddings)
4. **No Memory**: Each query is independent
5. **Single Language**: Primarily English

## 🌟 Possible Enhancements

1. **Vector Embeddings**: Use proper semantic search
2. **Multi-language**: Support French and Arabic
3. **Image Integration**: Show photos of attractions
4. **Map Integration**: Display locations visually
5. **Conversation Memory**: Remember context across questions
6. **Real-time Updates**: Fetch latest data from APIs
7. **Voice Input**: Speech-to-text integration
8. **Mobile App**: Native iOS/Android version

## 📝 License

This is an educational example. Feel free to use and modify for your own projects.

## 🤝 Contributing

To improve the Chad knowledge base:
1. Verify facts with reliable sources
2. Add citations where possible
3. Keep information objective and balanced
4. Test thoroughly before adding

## 📧 Support

For questions or issues, please refer to:
- Anthropic API docs: https://docs.anthropic.com
- Flask documentation: https://flask.palletsprojects.com

---

**Built with**: Claude Sonnet 4, Anthropic API, JavaScript, Python Flask

**Created**: February 2026

**Subject**: Republic of Chad, Africa 🇹🇩
