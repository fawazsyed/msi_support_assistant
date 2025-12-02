# Curated Motorola Documentation URLs for Prototype

## Purpose
Manually curated list of documentation URLs that are:
1. Publicly accessible
2. Contain useful technical content
3. Work well with web crawlers

## Usage
Copy URLs from this file into `SAMPLE_URLS` in `prototype_crawler.py`

## Documentation Sites

### docs.motorolasolutions.com
These are typically static/PDF-based and easier to crawl:

```
https://docs.motorolasolutions.com/bundle?labelkey=product_az_apx_4000
https://docs.motorolasolutions.com/bundle?labelkey=product_az_mototrbo_r7
https://docs.motorolasolutions.com/bundle?labelkey=product_az_wave_ptx
```

### Public Documentation/Guides
Add URLs you find by browsing:
- Product manuals (PDF links work well)
- Getting started guides
- Technical specifications

## Next Steps

1. **Browse** docs.motorolasolutions.com manually
2. **Copy** 10-20 useful document URLs
3. **Add** them to SAMPLE_URLS in prototype_crawler.py
4. **Run** the crawler again

## Alternative Approach

If public crawling remains difficult:
1. Focus on docs you can download (PDFs)
2. Use learning.motorolasolutions.com if available
3. Consider API access if Motorola provides it
4. For support articles, may need to handle authentication

## Learning Point

**Real-world web crawling often requires:**
- Manual URL curation for protected content
- Different strategies for different site types
- Respect for authentication/access controls
- Mix of automated + manual approaches
