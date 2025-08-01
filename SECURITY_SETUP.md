# 🔐 Security Setup Guide

## API Key Configuration

**⚠️ IMPORTANT**: Never commit actual API keys to version control!

### Quick Setup

1. **Copy the template**:
   ```bash
   cp .env.template .env
   ```

2. **Add your OpenAI API key**:
   - Open `.env` file
   - Replace `your-openai-api-key-here` with your actual OpenAI API key
   - Save the file

3. **Verify setup**:
   ```bash
   python -c "from config.phase1_settings import get_settings; print('✅ API key configured' if get_settings().OPENAI_API_KEY != 'your-openai-api-key-here' else '❌ Please set your API key')"
   ```

### Getting Your OpenAI API Key

1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Sign in to your OpenAI account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)
5. Paste it in your `.env` file

### Environment Variables

The `.env` file contains:
- `OPENAI_API_KEY`: Your OpenAI API key (required)
- Model configurations (optional, defaults provided)
- Database settings (optional, defaults to SQLite)
- Application settings (optional)

### Security Best Practices

✅ **DO**:
- Keep `.env` file local (never commit to git)
- Use different API keys for development/production
- Regularly rotate your API keys
- Set usage limits on your OpenAI account

❌ **DON'T**:
- Share API keys in chat, email, or documentation
- Commit `.env` files to version control
- Use production keys in development
- Leave unused API keys active

### Deployment

For production deployment:
- Use environment variables instead of `.env` files
- Use secrets management services
- Set up monitoring for API usage
- Implement API key rotation

### Troubleshooting

**"API key not found" error**:
1. Check if `.env` file exists
2. Verify `OPENAI_API_KEY` is set correctly
3. Ensure no extra spaces around the key
4. Restart the application after changes

**"Invalid API key" error**:
1. Verify the key is correct (starts with `sk-`)
2. Check if the key is active in OpenAI dashboard
3. Ensure sufficient credits in your OpenAI account