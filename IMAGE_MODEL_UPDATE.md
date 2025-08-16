# Image Model Update - GPT-Image-1

## Overview

The AI Social Media Platform has been updated to use OpenAI's latest image generation model: **`gpt-image-1`** (released April 23, 2025).

## What Changed

### Previous Configuration
- **Model**: `dall-e-3` or `dall-e-2`
- **Quality Options**: `standard`, `hd`
- **Size Options**: Limited to DALL-E specifications
- **Generation**: Single API call with `n` parameter

### New Configuration
- **Model**: `gpt-image-1`
- **Quality Options**: `low`, `medium`, `high`, `auto`
- **Size Options**: `1024x1024`, `1024x1536`, `1536x1024`
- **Generation**: One image per API call (multiple calls for multiple images)

## Updated Environment Variables

Add to your `.env` file:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-key-here
DEFAULT_OPENAI_MODEL=gpt-4o
OPENAI_IMAGE_MODEL=gpt-image-1  # Updated from dall-e-3
OPENAI_IMAGE_BASE_URL=https://api.openai.com/v1  # Standard OpenAI API endpoint
IMAGE_BASE_URL=http://localhost:8000  # Base URL for serving saved images
OPENAI_ORG_ID=org-your-org-id-here
```

## Important: gpt-image-1 Behavior

**Key Difference**: Unlike DALL-E, `gpt-image-1` **only returns base64-encoded images**, not direct URLs. The system automatically handles this by:

1. **For `response_format: "b64_json"`**: Returns the base64 data directly
2. **For `response_format: "url"`**: Automatically saves the base64 image to disk and returns a URL

This ensures backward compatibility with existing code while leveraging the new model's capabilities.

## Key Improvements

### 1. Enhanced Image Quality
- **Professional-grade output**: Higher quality, more detailed images
- **Better prompt following**: More accurate interpretation of complex prompts
- **Improved text rendering**: Better text-in-image capabilities

### 2. Advanced Features
- **World knowledge integration**: Leverages broader knowledge for context
- **Custom style guidelines**: Better adherence to brand guidelines
- **Versatile styles**: Supports diverse artistic and photographic styles

### 3. API Improvements
- **Flexible quality settings**: `auto` quality adapts to content
- **Better error handling**: More robust generation process
- **Enhanced metadata**: Richer response data

## Usage Examples

### Basic Image Generation
```python
# Via Image Worker
task = WorkerTask(
    task_id="image_gen_001",
    task_type="image_generation",
    input_data={
        "prompt": "A futuristic city skyline at sunset with flying cars",
        "size": "1024x1024",
        "quality": "high",  # New quality options
        "style": "photorealistic",
        "n_images": 1
    }
)

result = await image_worker.process_task(task)
```

### Social Media Optimized Images
```python
# Generate platform-specific images
social_image = await image_worker.generate_social_media_image(
    prompt="Professional headshot for LinkedIn profile",
    platform="linkedin",
    style="professional",
    size="1024x1024"
)
```

### Brand-Consistent Images
```python
# Generate brand-aligned visuals
brand_image = await image_worker.generate_brand_image(
    prompt="Modern office workspace with productivity tools",
    brand_colors=["#1DA1F2", "#FFFFFF"],
    brand_style="minimalist",
    size="1536x1024"
)
```

## Migration Notes

### Automatic Migration
- **No code changes required**: The system automatically uses the new model
- **Backward compatibility**: Existing prompts work with improved results
- **Quality mapping**: Old quality settings are automatically converted

### Performance Considerations
- **Multiple images**: Now requires multiple API calls (handled automatically)
- **Rate limiting**: Consider delays between requests for bulk generation
- **Costs**: New pricing structure based on token usage

### Quality Settings Migration
```python
# Old DALL-E settings → New gpt-image-1 settings
"standard" → "medium"
"hd" → "high"
# New options: "low", "auto"
```

## Pricing (as of August 2025)

- **Text Input Tokens**: $5 per 1M tokens
- **Image Input Tokens**: $10 per 1M tokens  
- **Image Output Tokens**: $40 per 1M tokens

*Note: Pricing varies by image quality and size. See [OpenAI pricing](https://openai.com/pricing) for details.*

## Safety & Compliance

### Built-in Safety
- **Content moderation**: Automatic filtering of inappropriate content
- **C2PA metadata**: Embedded provenance information in generated images
- **Usage policies**: Compliance with OpenAI's usage guidelines

### Customizable Moderation
```python
# Adjust moderation sensitivity
payload = {
    "model": "gpt-image-1",
    "prompt": "Your prompt here",
    "moderation": "strict"  # Options: strict, moderate, relaxed
}
```

## Testing the Update

### 1. Verify Configuration
```bash
# Check environment variables
echo $OPENAI_IMAGE_MODEL  # Should output: gpt-image-1
```

### 2. Test Image Generation
```python
# Test via API endpoint
curl -X POST http://localhost:8000/api/images/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Test image generation with gpt-image-1",
    "quality": "high",
    "size": "1024x1024"
  }'
```

### 3. Frontend Integration
- Navigate to `/dashboard/create`
- Use the AI image generation feature
- Verify higher quality output and better prompt adherence

## Troubleshooting

### Common Issues

1. **API Key Issues**
   ```bash
   # Verify API key has access to gpt-image-1
   curl -H "Authorization: Bearer $OPENAI_API_KEY" \
        https://api.openai.com/v1/models
   ```

2. **Quality Parameter Errors**
   - Use: `low`, `medium`, `high`, `auto`
   - Avoid: `standard`, `hd` (old DALL-E parameters)

3. **Size Parameter Errors**
   - Supported: `1024x1024`, `1024x1536`, `1536x1024`
   - Unsupported sizes will default to `1024x1024`

### Performance Optimization

1. **Batch Processing**: For multiple images, implement proper delays
2. **Quality Selection**: Use `auto` for optimal quality/cost balance
3. **Caching**: Cache generated images to avoid regeneration

## Benefits Summary

✅ **Higher Quality**: Professional-grade image generation  
✅ **Better Accuracy**: Improved prompt interpretation  
✅ **Enhanced Features**: Text rendering, style consistency  
✅ **Flexible Options**: More quality and size choices  
✅ **Safety Built-in**: Automatic content moderation  
✅ **Future-Proof**: Latest OpenAI technology  

---

**The update to gpt-image-1 significantly enhances the image generation capabilities of your AI Social Media Platform, providing better quality, more accurate results, and advanced features for professional content creation.**
