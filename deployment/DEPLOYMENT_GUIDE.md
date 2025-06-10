# 🚀 Streamlit Cloud Deployment Guide

## GAI Final Project - Multi-Agent Recruitment Chatbot

This guide provides step-by-step instructions for deploying the multi-agent recruitment chatbot to Streamlit Cloud.

---

## 📋 Prerequisites

### 1. Project Requirements
- ✅ Complete project with all Phase 3 components
- ✅ Working Streamlit application
- ✅ GitHub repository with latest code
- ✅ OpenAI API key with credits
- ✅ Environment variables configured

### 2. Required Accounts
- **GitHub Account**: For repository hosting
- **Streamlit Cloud Account**: For deployment (free tier available)
- **OpenAI Account**: For API access and embeddings

---

## 🛠️ Pre-Deployment Setup

### Step 1: Run Deployment Setup Script

```bash
cd deployment
python deploy_setup.py
```

This script will:
- ✅ Validate project structure
- ✅ Check dependencies
- ✅ Create configuration files
- ✅ Generate deployment report
- ✅ Create secrets template

### Step 2: Prepare Repository

```bash
# Ensure all changes are committed
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

### Step 3: Verify File Structure

Ensure your project has this structure:

```
gai_final_project-1/
├── .streamlit/
│   └── config.toml                 # Streamlit configuration
├── deployment/
│   ├── streamlit_config.toml       # Deployment config
│   ├── requirements_streamlit.txt  # Cloud-optimized dependencies
│   ├── streamlit_secrets_template.toml  # Secrets template
│   └── deploy_setup.py            # Setup script
├── streamlit_app/
│   ├── streamlit_main.py          # Main app entry point
│   └── components/                # UI components
├── app/                           # Core application
├── data/                          # Data files
├── requirements.txt               # Main requirements
└── packages.txt                   # System packages (if needed)
```

---

## 🌐 Streamlit Cloud Deployment

### Step 1: Create Streamlit Cloud App

1. **Visit Streamlit Cloud**: https://share.streamlit.io/
2. **Sign in** with your GitHub account
3. **Click "New app"**
4. **Connect your repository**:
   - Repository: `your-username/gai_final_project-1`
   - Branch: `main`
   - Main file path: `streamlit_app/streamlit_main.py`

### Step 2: Configure App Settings

#### Advanced Settings:
- **Python version**: `3.11`
- **Requirements file**: `requirements.txt`
- **Additional files**: `packages.txt` (if system packages needed)

### Step 3: Set Environment Secrets

Go to **App Settings → Secrets** and add:

```toml
# Copy from deployment/streamlit_secrets_template.toml
OPENAI_API_KEY = "your-actual-openai-api-key"
DATABASE_URL = "sqlite:///./data/recruitment_bot.db"
VECTOR_STORE_TYPE = "openai"
OPENAI_ASSISTANT_ID = "your-assistant-id"
OPENAI_FILE_ID = "your-file-id"
DEBUG_MODE = "false"
```

⚠️ **Important**: Replace template values with your actual API keys and IDs

### Step 4: Deploy

1. **Click "Deploy"**
2. **Wait for build** (usually 2-5 minutes)
3. **Monitor logs** for any errors
4. **Test functionality** once deployed

---

## 🔧 Configuration Details

### Streamlit Configuration (`config.toml`)

Key settings for cloud deployment:

```toml
[global]
developmentMode = false

[server]
port = 8501
enableCORS = false
enableXsrfProtection = true
fileWatcherType = "none"
maxUploadSize = 50

[client]
showErrorDetails = false

[runner]
magicEnabled = true
fastReruns = true
```

### Dependencies Optimization

The `deployment/requirements_streamlit.txt` includes:
- **Core**: Streamlit, LangChain, OpenAI
- **Database**: SQLAlchemy, ChromaDB
- **Processing**: Pandas, NumPy
- **Visualization**: Plotly, Matplotlib
- **Optimizations**: Version constraints for stability

---

## 🔐 Security Best Practices

### Environment Variables
- ✅ **Never commit API keys** to repository
- ✅ **Use Streamlit secrets** for sensitive data
- ✅ **Set appropriate access levels**
- ✅ **Regularly rotate API keys**

### Application Security
- ✅ **Disable development mode** in production
- ✅ **Enable XSRF protection**
- ✅ **Hide error details** from users
- ✅ **Validate all inputs**

---

## 🧪 Testing Deployment

### Step 1: Functional Testing

Once deployed, test these features:

1. **Chat Interface**:
   - ✅ Send messages and receive responses
   - ✅ Test all conversation flows
   - ✅ Verify agent routing (INFO, SCHEDULE, END)

2. **Info Advisor**:
   - ✅ Ask job-related questions
   - ✅ Verify vector search responses
   - ✅ Check source references

3. **Scheduling**:
   - ✅ Request interview scheduling
   - ✅ Select time slots
   - ✅ Confirm appointments

4. **Admin Panel**:
   - ✅ View conversation analytics
   - ✅ Check performance metrics
   - ✅ Export functionality

### Step 2: Performance Testing

- ✅ **Response times** < 5 seconds
- ✅ **Memory usage** within limits
- ✅ **Error handling** graceful
- ✅ **Concurrent users** support

### Step 3: Load Testing

For production deployment:
- Test with multiple concurrent users
- Monitor resource usage
- Check database performance
- Verify vector search speed

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Import Errors
```
ModuleNotFoundError: No module named 'xyz'
```
**Solution**: Check `requirements.txt` has all dependencies

#### 2. Environment Variable Issues
```
KeyError: 'OPENAI_API_KEY'
```
**Solution**: Verify secrets are set in Streamlit Cloud

#### 3. Database Errors
```
sqlite3.OperationalError: no such table
```
**Solution**: Ensure database initialization runs correctly

#### 4. Vector Store Issues
```
OpenAI API Error: File not found
```
**Solution**: Verify `OPENAI_FILE_ID` in secrets

### Debug Mode

For troubleshooting, temporarily set:
```toml
DEBUG_MODE = "true"
```

This enables:
- Detailed error messages
- Debug logging
- Development features

---

## 📊 Monitoring & Maintenance

### Performance Monitoring

1. **Streamlit Cloud Metrics**:
   - Resource usage
   - Response times
   - Error rates

2. **Application Logs**:
   - Agent decisions
   - API calls
   - User interactions

3. **Custom Metrics**:
   - Conversation success rates
   - Agent performance
   - User satisfaction

### Regular Maintenance

- **Weekly**: Check logs for errors
- **Monthly**: Update dependencies
- **Quarterly**: Review performance metrics
- **As needed**: Rotate API keys

---

## 🎯 Optimization Tips

### Performance
- Use caching for expensive operations
- Optimize vector database queries
- Minimize API calls
- Use session state efficiently

### User Experience
- Fast response times
- Clear error messages
- Intuitive interface
- Mobile-friendly design

### Cost Management
- Monitor OpenAI API usage
- Optimize embedding storage
- Use efficient prompts
- Cache common responses

---

## 📞 Support & Resources

### Documentation
- [Streamlit Cloud Docs](https://docs.streamlit.io/streamlit-cloud)
- [LangChain Documentation](https://python.langchain.com/)
- [OpenAI API Reference](https://platform.openai.com/docs)

### Community
- [Streamlit Community Forum](https://discuss.streamlit.io/)
- [LangChain Discord](https://discord.gg/langchain)
- [OpenAI Community](https://community.openai.com/)

---

## 🎉 Success Checklist

Before considering deployment complete:

- [ ] ✅ App loads without errors
- [ ] ✅ All features working correctly
- [ ] ✅ Performance meets requirements
- [ ] ✅ Security measures in place
- [ ] ✅ Monitoring configured
- [ ] ✅ Documentation updated
- [ ] ✅ Team trained on maintenance

---

**🚀 Your multi-agent recruitment chatbot is now live on Streamlit Cloud!**

Share your deployment URL and start recruiting Python developers with AI assistance! 