# FUNCTION CODE
from google.cloud import secretmanager
from google.cloud import bigquery
# from transformers import pipeline
from PIL import Image
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from langchain.llms import OpenAI
from langchain.agents.tools import Tool
from langchain import OpenAI, PromptTemplate
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.chat_models import ChatOpenAI
from langchain.tools import tool
from langchain.document_loaders import PyPDFLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.output_parsers import PydanticOutputParser
from langchain.vectorstores.pinecone import Pinecone
from langchain.schema import SystemMessage, HumanMessage
import re
import json
import pinecone
from bs4 import BeautifulSoup
import requests
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from pydantic import BaseModel, Field
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
import base64
import uuid
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./patent-search-390320-b508c64f5340.json"

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

# set OpenAI Key
client = secretmanager.SecretManagerServiceClient()
openai_key = client.access_secret_version(request={"name": f"projects/704330884622/secrets/openai_key/versions/latest"}).payload.data.decode("utf-8")
os.environ['OPENAI_API_KEY'] = openai_key

# set google credentials

# lazy loading of image to text model
# image_to_text = None

# set up pinecone
pinecone_key = client.access_secret_version(request={"name": f"projects/704330884622/secrets/pinecone_key/versions/latest"}).payload.data.decode("utf-8")
pinecone.init(api_key=pinecone_key)

# set up embeddings
embeddings = OpenAIEmbeddings()

# set up pydantic object
class VectorList(BaseModel):
    vqueries: list[str] = Field(description="list of vector search queries focusing on different aspects of the idea that could be used to search for similar patents")

# pdf generation stuff
class CustomDivider(Flowable):
    def __init__(self, width=1, color=colors.lightgrey):
        Flowable.__init__(self)
        self.width = width
        self.color = color
    
    def wrap(self, availWidth, availHeight):
        return (availWidth, self.width)
    
    def draw(self):
        self.canv.saveState()
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.width)
        self.canv.line(-80, 0, letter[0] - 80, 0)  # Starts from -80 pixels
        self.canv.restoreState()

# search patent tool
@tool
def search_patents(sql_query: str) -> str:
    """Gets relevant patents based on a query. Your input should just be the BigQuery SQL Query. Your query should begin with 
        SELECT
            publication_number,
            title_localized.text AS title
        FROM
            `patents-public-data.patents.publications`,
            UNNEST(title_localized) AS title_localized"""
    client = bigquery.Client(project="patent-search-390320")
    
    
    # Execute the query
    query_job = client.query(sql_query)
    
    # Store the results
    results = []
    for row in query_job:
        results.append({'publication_number': row.publication_number, 'title': row.title})

    return json.dumps(results)

def get_patent_pdf_url(publication_id):
    base_url = 'https://patents.google.com/patent/'

    # Function to find PDF URL
    def try_find_pdf_url(url):
        response = requests.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            pdf_link = None
            for link in soup.find_all('a'):
                href = link.get('href')
                if href and href.endswith('.pdf'):
                    pdf_link = href
                    break

            return pdf_link
        else:
            return None

    url = f"{base_url}{publication_id}"
    pdf_url = try_find_pdf_url(url)
    if not pdf_url:
        # If the find fails, modify the publication ID and try again
        match = re.match(r'(\D+)(\d{4})(\d*)(\D+)', publication_id)
        if match:
            new_publication_id = f"{match.group(1)}{match.group(2)}0{match.group(3)}"
            new_url = f"{base_url}{new_publication_id}"
            pdf_url = try_find_pdf_url(new_url)
            if not pdf_url:
                # If still fails, remove the end of the publication ID and try again
                new_publication_id = f"{match.group(1)}{match.group(2)}0{match.group(3)}"
                new_url = f"{base_url}{new_publication_id}"
                pdf_url = try_find_pdf_url(new_url)
                if not pdf_url:
                    print("Failed to find the PDF URL with the modified publication ID.")
            else:
                print("Failed to find the PDF URL with the original publication ID.")

    return pdf_url

@app.route('/get_pdf', methods=['POST'])
def main():
    global image_to_text

    # # handle CORS preflight
    # if request.method == 'OPTIONS':
    #     headers = {
    #         'Access-Control-Allow-Origin': '*',
    #         'Access-Control-Allow-Methods': 'GET',
    #         'Access-Control-Allow-Headers': 'Content-Type',
    #         'Access-Control-Max-Age': '3600'
    #     }

    #     return ('', 204, headers)

    # # set CORS return headers
    # cors_headers = {
    #     'Access-Control-Allow-Origin': '*'
    # }

    # lazy load image to text model
    # if not image_to_text:
    #     image_to_text = pipeline("image-to-text", model="nlpconnect/vit-base-patch16-224-in21k", device=0)

    # convert images to text
    request_json = request.get_json()
    images = request_json['images']
    image_text = []
    for image in images:
        image = Image.open(image)
        image_text.append(image_to_text(image)[0]['generated_text'])

    # add images to idea
    image_txts = '\n\t- '.join(image_text)
    idea_processed = request_json['idea']#f"{request_json['idea']} \ndescription of figures:\n{image_txts}"

    # set up agent to find patents similar to the user's idea
    tools = [
        Tool(
            name="SearchPatents",
            func=search_patents.run,
            description="""Gets relevant patents based on a query. Your input should just be the BigQuery SQL Query. Your query should begin with SELECT
            publication_number,
            title_localized.text AS title
        FROM
            `patents-public-data.patents.publications`,
            UNNEST(abstract_localized) AS abstract_localized, UNNEST(title_localized) AS title_localized WHERE abstract_localized.text LIKE

        Only search for 10 patents at a time. Be sure to use OR instead of AND. Search for a variety of keywords related to the idea until you find at least similar patents.
        """
        )
    ]
    mrkl = initialize_agent(tools, ChatOpenAI(temperature=0, model="gpt-4-0613"), agent=AgentType.OPENAI_FUNCTIONS, verbose=True)
    
    # get patent results
    try:
        output = mrkl.run(
            f"Search patents related to my idea of {idea_processed}."
        )
        pattern = re.compile(r'\b[A-Z]{2}-\d{4,}-[A-Z0-9]{1,}\b')
        patent_ids = pattern.findall(output)

        def remove_dashes(publication_id):
            return publication_id.replace('-', '')
        
        patent_ids = list(map(remove_dashes, patent_ids))
    except Exception as e:
        return jsonify({"error": f"Exception getting patents from bigquery {str(e)}"}), 500

    # get patent pdf urls
    try:
        session_id = str(uuid.uuid4())
        pages = []
        id_urls = {}

        def get_pages(patent_id):
            pdf_url = get_patent_pdf_url(remove_dashes(patent_id))
            if pdf_url:
                id_urls[patent_id] = pdf_url
                loader = PyPDFLoader(pdf_url)
                pages_temp = loader.load_and_split()
                for i in range(len(pages_temp)):
                    pages_temp[i].metadata = {
                        "patent_id": patent_id,
                    }
                return pages_temp

        # for patent_id in patent_ids:
        #     pdf_url = get_patent_pdf_url(remove_dashes(patent_id))
        #     if pdf_url:
        #         id_urls[patent_id] = pdf_url
        #         loader = PyPDFLoader(pdf_url)
        #         pages_temp = loader.load_and_split()
        #         for i in range(len(pages_temp)):
        #             pages_temp[i].metadata = {
        #                 "patent_id": patent_id,
        #             }
        #         pages.extend(pages_temp)
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(get_pages, patent_id) for patent_id in patent_ids]
            for future in as_completed(futures):
                pages.extend(future.result())

        vectordb = Pinecone.from_documents(pages, embeddings, index_name="patents", namespace=session_id)
    except Exception as e:
        return jsonify({"error": f"Exception creating vector database {str(e)}"}), 500

    # get patent snippets from vector DB
    try:
        vsearch_llm = OpenAI(temperature=0)
        parser = PydanticOutputParser (pydantic_object=VectorList)
        prompt = PromptTemplate(
            template="Based on the following idea, generate a JSON list of vector search queries focusing on different aspects of the idea that could be used to search for similar patents, then return them as a JSON list in the following format: \n{format_instructions} \n\n{idea}",
            input_variables=["idea"],
            partial_variables={"format_instructions": parser.get_format_instructions ()}
        )

        _input = prompt.format_prompt(idea=idea_processed).to_string()

        queries = parser.parse(vsearch_llm(_input)).vqueries
        patents = []
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(vectordb.similarity_search, query, 1, None, session_id): query for query in queries}
            for future in as_completed(futures):
                patents.extend([f"patent {patent.metadata['patent_id']}: \n {patent.page_content}" for patent in future.result()])
    except Exception as e:
        return jsonify({"error": f"Exception searching vector db for patents {str(e)}"}), 500

    # use GPT-4 to generate the detailed analysis, suggestions for improvement, and score.
    gpt4_messages = [
        [[
            SystemMessage(content=f"Based on the following idea, generate an at least two-paragraph-long detailed analysis on the IP landscape surrounding the idea and relevant patents and how the idea is similar/different. Go into specifics about what the existing patents have to offer. Excerpts from the existing patents making up the IP landscape are below: \n\n{patents}"),
            HumanMessage(content=idea_processed)
        ], "analysis"],
        [[
            SystemMessage(content=f"Based on the following idea, give a score from 0 to 100 summarizing how patentable the idea is, with 0 being that the patent would definitely not be approved, 100 that it would be approved with no revisions, and 50 that it the patent could potentially be approved but would definitely require revisions. This score should be based on the detail of the idea, the IP landscape, and how novel the idea is.Excerpts from the existing patents making up the IP landscape are below: \n\n{patents} \n\n RETURN ONLY THE NUMERICAL SCORE."),
            HumanMessage(content=idea_processed)
        ], "score"],
        [[
            SystemMessage(content=f"Based on the following idea, give at least 3 suggestions on how to improve the idea to make it more patentable. Write a paragraph for each suggestion, and make the headings of each suggestion bold by surrounding them with <b> tags. Excerpts from the existing patents making up the IP landscape are below: \n\n{patents}"),
            HumanMessage(content=idea_processed)
        ], "suggestions"]
    ]

    try:
        gpt4_llm = ChatOpenAI(temperature=0, model="gpt-4")

        # get analysis
        analysis_messages = [
            SystemMessage(content=f"Based on the following idea, generate an at least two-paragraph-long detailed analysis on the IP landscape surrounding the idea and relevant patents and how the idea is similar/different. Go into specifics about what the existing patents have to offer. Excerpts from the existing patents making up the IP landscape are below: \n\n{patents}"),
            HumanMessage(content=idea_processed)
        ]
        analysis = gpt4_llm(analysis_messages).content

        # get suggestions
        suggestions_messages = [
            SystemMessage(content=f"Based on the following idea, give at least 3 suggestions on how to improve the idea to make it more patentable. Write a paragraph for each suggestion, and make the headings of each suggestion bold by surrounding them with <b> tags. An analysis of the IP landscape is below: \n\n{analysis}"),
            HumanMessage(content=idea_processed)
        ]
        suggestions = gpt4_llm(suggestions_messages).content

        # get score
        score_messages = [
            SystemMessage(content=f"Based on the following idea, give a score from 0 to 100 summarizing how patentable the idea is, with 0 being that the patent would definitely not be approved, 100 that it would be approved with no revisions, and 50 that it the patent could potentially be approved but would definitely require revisions. This score should be based on the detail of the analysis of the IP landscape and suggestions for improvement. If the existing patents arent strognly related to the idea or the suggestions for improvement are minor (or both), give a high score and vice versa. An analysis of the IP landscape and suggestions for improvement are below: \n\n{analysis} \n{suggestions}\n RETURN ONLY THE NUMERICAL SCORE."),
        ]
        score = gpt4_llm(score_messages).content

        # responses = {}
        # with ThreadPoolExecutor() as executor:
        #     futures = {executor.submit(gpt4_llm, messages): msg_type for messages, msg_type in gpt4_messages}
        #     for future in as_completed(futures):
        #         msg_type = futures[future]
        #         output = future.result().content
        #         responses[msg_type] = output
    except Exception as e:
        return jsonify({"error": f"Exception generating report text: {str(e)}"}), 500

    # generate the pdf
    try:
        idea_sleuth_score = int(score)#int(responses['score'])
        detailed_analysis = analysis#responses['analysis']
        suggestions = suggestions#responses['suggestions']
        if idea_sleuth_score >= 80:
            score_color = colors.green
        elif idea_sleuth_score >= 50:
            score_color = colors.orange
        else:
            score_color = colors.red

        def draw_top_bar(canvas, doc, score_color):
            canvas.saveState()
            canvas.setFillColor(score_color)
            canvas.rect(0, letter[1] - 0.5*inch, letter[0], 0.5*inch, fill=1, stroke=0)
            canvas.restoreState()

        def on_first_page(canvas, doc):
            draw_top_bar(canvas, doc, score_color)

            box_size = 40
            padding = 5
            radius = 8
            border_thickness = 2
            box_top = letter[1] - 0.5*inch - 10
            canvas.saveState()
            canvas.setStrokeColor(score_color)
            canvas.setLineWidth(border_thickness)
            canvas.roundRect(20, box_top - box_size, box_size, box_size, radius)
            canvas.drawImage("emoji.png", 20 + padding, box_top - box_size + padding + border_thickness/2, width=box_size - 2*padding - border_thickness, height=box_size - 2*padding - border_thickness, mask='auto')
            canvas.restoreState()

            score_box_width = 60
            score_box_height = 40
            radius = 8
            score_box_left = letter[0] - 80  # position the score box on the right
            canvas.saveState()
            canvas.setStrokeColor(score_color)
            canvas.setFillColor(score_color)
            canvas.roundRect(score_box_left, box_top - score_box_height, score_box_width, score_box_height, radius, fill=1, stroke=1)
            
            score_text = str(idea_sleuth_score)
            text_width = canvas.stringWidth(score_text, "Helvetica-Bold", 18)
            text_x = score_box_left + (score_box_width - text_width) / 2
            text_y = box_top - score_box_height + (score_box_height - 18) / 2
            canvas.setFillColor(colors.white)
            canvas.setFont("Helvetica-Bold", 18)
            canvas.drawString(text_x, text_y, score_text)
            canvas.restoreState()

        def on_later_pages(canvas, doc):
            draw_top_bar(canvas, doc, score_color)

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)

        styles = getSampleStyleSheet()
        header_style = ParagraphStyle('HeaderStyle', fontName='Helvetica-Bold', fontSize=20, fontWeight=900, alignment=0, spaceAfter=6, leftIndent=-60)  # alignment 0 is for left alignment
        subtitle_style = ParagraphStyle('SubtitleStyle', fontSize=12, alignment=0, spaceAfter=12, leftIndent=-60)  # alignment 0 is for left alignment
        idea_style = ParagraphStyle('IdeaStyle', fontName='Helvetica-Bold', fontSize=12, alignment=0, spaceAfter=6, leftIndent=-60)  # alignment 0 is for left alignment
        text_style = ParagraphStyle('TextStyle', fontSize=10, alignment=0, spaceAfter=6, leftIndent=-60)

        related_patents = ""
        for key in id_urls:
            related_patents += "- " + key + ": " + id_urls[key] + "<br/>"

        content = [
            Spacer(1, 0.5*inch),
            Paragraph('Your Idea Report', header_style),
            Spacer(1, 0.1*inch),
            Paragraph('By IdeaSleuth', subtitle_style),
            Spacer(1, 0.3*inch),
            Paragraph('YOUR IDEA', idea_style),
            Paragraph(request_json['idea'], text_style),
            Spacer(1, 0.2*inch),
            CustomDivider(),
            Spacer(1, 0.3*inch),
            Paragraph('RELATED INTELLECTUAL PROPERTY', idea_style),
            Paragraph(related_patents, text_style),
            Spacer(1, 0.2*inch),
            CustomDivider(),
            Spacer(1, 0.3*inch),
            Paragraph('DETAILED ANALYSIS', idea_style),
            Paragraph(detailed_analysis.replace("\n", "<br/>"), text_style),
            Spacer(1, 0.2*inch),
            CustomDivider(),
            Spacer(1, 0.3*inch),
            Paragraph('SUGGESTIONS TO IMPROVE SCORE', idea_style),
            Paragraph(suggestions.replace("\n", "<br/>"), text_style),
            Spacer(1, 0.2*inch),
            CustomDivider()
        ]

        doc.build(content, onFirstPage=on_first_page, onLaterPages=on_later_pages)

        return jsonify(base64.b64encode(buffer.getvalue()).decode('utf-8')), 200
    except Exception as e:
        return jsonify({"error": f"Exception generating pdf: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)