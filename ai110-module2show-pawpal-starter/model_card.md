## AI Collaboration 

I knew I wanted to implement some sort of chatbot that utilizes Retrieval Augmented Generation. I asked Claude for some ideas, one of which was a pet health specific one. I prompted it for each step of the simple implementation starting from the data in the knowledge base to the rag pipeline itself. Honestly, every suggestion it gave was a very helpful one. 

## Testing Summary

- The RAG chabot was not tested with automated tests because it requires a live Gemini API key and network access. Manual testing was used instead by comparing response to hard-coded FAQ in database. 
- The knowledge base is manually curated and small. Edge-case symptom descriptions (uncommon or really specific illnesses) may retrieve a low-similarity FAQ and produce generic or even wrong advice.

---

## Reflection

Working with the RAG pipeline clarified the difference between retrieval quality and generation quality. A great LLM response based off a poorly matched FAQ is still wrong. For example, I asked "How do I tell if my cat is in heath" and it matched with "My dog seems overheated after being outside. What are signs of heatstroke?", which was tagged as an emergency. Those two are very different questions and require differnt responses. But because there was not a stronger match in the data, that was the output. That's why I had Claude add a drop down menu where you can see which question was the strongest match. This showed me how I would need to think carefully about the knowledge base structure and retrieval text (combining the FAQ question with its tags) in the future.

I was surprised that the LLM generation didn't just take over and state things that were not from the strongest FAQ response. 