import os
from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI
client = OpenAI(api_key=os.getenv('GROQ_API_KEY'), base_url='https://api.groq.com/openai/v1')

query = 'What is the core architecture of ResNet'
context = '''
--- Source: ResNet_Paper.pdf ---
## 4.2. CIFAR-10 and Analysis
The plain/residual architectures follow the form in Fig. 3 (middle/right). The network inputs are 32 x 32 images, with the per-pixel mean subtracted. The first layer is 3 x 3 convolutions. Then we use a stack of 6 n layers with 3 x 3 convolutions on the feature maps of sizes { 32 , 16 , 8 } respectively, with 2 n layers for each feature map size. The numbers of filters are { 16 , 32 , 64 } respectively. The subsampling is performed by convolutions with a stride of 2. The network ends with a global average pooling, a 10-way fully-connected layer, and softmax. There are totally 6 n +2 stacked weighted layers. 

--- Source: ResNet_Paper.pdf ---
## 3.3. Network Architectures
Residual Network. Based on the above plain network, we insert shortcut connections (Fig. 3, right) which turn the network into its counterpart residual version. The identity shortcuts (Eqn.(1)) can be directly used when the input and output are of the same dimensions (solid line shortcuts in Fig. 3).
'''

system_prompt = (
    "You are an intelligent enterprise search assistant (WorkIQ). "
    "Use the provided document excerpts below to answer the user's question. "
    "Synthesize the information provided to give a comprehensive answer. "
    "If the excerpts are completely unrelated and do not contain enough information to form an answer, say 'I cannot answer this based on the retrieved documents.'\n\n"
    f"CONTEXT:\n{context}"
)

try:
    response = client.chat.completions.create(
        model='llama-3.1-8b-instant',
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': query}
        ],
        temperature=0.0
    )
    print("RESPONSE:", response.choices[0].message.content)
except Exception as e:
    print('ERROR:', e)
