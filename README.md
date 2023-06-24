# IdeaSleuth

This is Mark Bruckert and Owen Burns submission to the Pinecone Hackathon, called IdeaSleuth. The original repo was created on Monday, but we created this new one because there might have been a key or two (oops!) in the original repo and we didn't want to make that public. Anyways... we hope you enjoy the project!

The main code for the project can be found in main.py

Additional experimentation can be found in Experimentation_Notebook_Logic.py and Experimentation_Notebook_Image.py (this contains the WIP image searching code that we mention in our submission).

## Inspiration

We run a startup and have a consistent problem of coming up with new ideas and wondering if anyone has ever built this before and if the idea already has already been patented. This leads to hours of searching around the internet and various patent databases to see what's out there when we could spend this time building new features, finding customers, and making money for our business. This is undoubtedly a process that costs businesses a lot of money, in fact according to UpCouncil, **each patent search can cost between $100 to $3000**, depending on the complexity. If we look at a product like the recently-announced Apple Vision Pro, 5,000 patents were filed for this **one product**.  Assuming each of these patents were extremely advanced due to their deeply technical nature, patent searches for the Vision Pro costed Apple **$15,000,000**. This might be a drop in the bucket for Apple, but for startups and much smaller companies, this is simply unattainable and might lead to valuable IP being left unprotected.

## What it does

IdeaSleuth generates an Intellectual Property/Existing Patent Briefing based on an idea that you have. Our project takes a description, finds, and reads patents from across the globe that are relevant (in any language!), and generates a PDF with the related patents, a detailed analysis of the IP landscape, suggestions to improve your idea, and even a score or how patentable your idea is!

You can try it out [here](https://idea-sleuth.vercel.app/)!

## How we built it

IdeaSleuth takes a description of an idea from the user and uses an LLM-powered agent (built with Langchain) to take this description and convert it into a series of SQL queries which is used to search the BigQuery database of international patents. Once relevant patents have been found, IdeaSleuth scrapes the Google Patent page for the patent in order to get the PDF, and loads all of the PDFs into our Pinecone vector database. From here, we use a GPT-4 agent to run a similarity search on our Pinecone database and answer the pre-set selection of questions, as well as assign the idea on a rating of how patentable it is. Once all of this information has been written, we use the reportlab python library to generate a stylish PDF which makes it easy to quickly consume all of the analysis about your idea and relevant IP. The front end for the application is built with React and hosted on Vercel.

## Challenges we ran into

We had a hard time getting IdeaSleuth to pull the correct relevant patents because we are generating SQL queries using an LLM and it was difficult to determine what queries are going to successfully return any patents let alone the right ones. We solved this problem by setting up a Langchain agent which is prompted to continuously generate and run new SQL queries, varying its query each time to be either different or broader until it finds enough relevant IP.

## Accomplishments that we're proud of

We are proud of the entire project, but especially the amount of prompt engineering that went into the patent search agent, the stylish pdf generation, and the ease of use that the front end provides to users.

## What's next for IdeaSleuth

We were hoping to add the ability for users to be able to upload their own sketches of their idea and run a similarity search on a pinecone database of patent sketches converted to vectors. This way, the PDF could contain images from patents that were similar to what you are building. However, we ran out of time and were not able to finish that, but definitely plan to add this feature soon!

## Usage of Pinecone

Without Pinecone, our product would not be possible. The similarity search empowered by the vectorization (and Pinecone of course!) of patent documents is what allows us to provide relevant information to the LLM and generate relevant analysis and the patentability score. Without this, we would be regularly hitting context limits when using GPT-4, or we would have to summarize chunks of each patent and combine these summaries, a process which would not only take an unrealistic amount of time, but also would cost a lot of money. Using Pinecone's solutions, the product is able to be quick, but most importantly free!

We also started working on a portion of the project that vectorized patent sketches, uploaded them to a Pinecone index, and then ran a similarity search comparing the user's uploaded sketches to those found in the relevant patents. 

## Partner's Products that We Utilized
1. Pinecone Vector Database
2. Langchain Agents (OpenAI Functions Agent), LLM wrappers, Document Loaders, and Output Parsers
3. A variety of OpenAI language models (including gpt-4 and text-embedding-ada-002)
4. Vercel Hosting
