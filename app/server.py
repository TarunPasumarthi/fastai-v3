import aiohttp
import asyncio
import uvicorn
from fastai import *
from fastai.vision import *
from io import BytesIO
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles
import zipfile
from deploy_gpt2 import main
from vars import *

#export_file_url = 'https://www.googleapis.com/drive/v3/files/1kncQ_Nt-LHfGQrIAF_tlmgyVkuIRwqNO?alt=media&key=AIzaSyCwAreaXcbtPfMsDQRpwLgS0uKNWxxvhKU'
#export_file_name = 'politics_100000_stage2.pkl'
#export_file_url = 'https://www.dropbox.com/s/6bgq8t6yextloqp/export.pkl?raw=1'
#export_file_name = 'export.pkl'

classes = ['r/politics']
path = Path(__file__).parent

app = Starlette()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_headers=['X-Requested-With', 'Content-Type'])
app.mount('/static', StaticFiles(directory='app/static'))

ufmodels={}

async def download_file(url, dest):
    if dest.exists(): return
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
            with open(dest, 'wb') as f:
                f.write(data)


async def setup_learner(model,export_file_url,export_file_name):
    export_file_name=str(export_file_name)
    await download_file(export_file_url, path / export_file_name)
    try:
        if(model=="ULMFit"):
            learn = load_learner(path, export_file_name)
            return learn
        elif(model=="GPT-2"):
            pstring=export_file_name[:-9]+"_100000/"
            cpath=path / pstring
            if not cpath.exists():
                fname=path / export_file_name
                with zipfile.ZipFile(fname, 'r') as zip_ref:
                    zip_ref.extractall(path)
    except RuntimeError as e:
        if len(e.args) > 0 and 'CPU-only machine' in e.args[0]:
            print(e)
            message = "\n\nThis model was trained with an old version of fastai and will not work in a CPU environment.\n\nPlease update the fastai library in your training environment and export your model again.\n\nSee instructions for 'Returning to work' at https://course.fast.ai."
            raise RuntimeError(message)
        else:
            raise

for key in ulmfit:
    export_file_url=ulmfit[key]
    export_file_name=key[2:].lower()+"_100000_stage2.pkl"
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop=asyncio.get_event_loop()
    tasks = [asyncio.ensure_future(setup_learner("ULMFit",export_file_url,export_file_name))]
    learn = loop.run_until_complete(asyncio.gather(*tasks))[0]
    ufmodels[key]=learn
    loop.close()

for key in gpt2:
    export_file_url=gpt2[key]
    export_file_name=key[2:].lower()+"_gpt2.zip"
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop=asyncio.get_event_loop()
    tasks = [asyncio.ensure_future(setup_learner("GPT-2",export_file_url,export_file_name))]
    learn = loop.run_until_complete(asyncio.gather(*tasks))[0]
    loop.close()


@app.route('/')
async def homepage(request):
    html_file = path / 'view' / 'index.html'
    return HTMLResponse(html_file.open().read())


@app.route('/analyze', methods=['POST'])
async def analyze(request):
    form_data = await request.form()
    sentence = form_data['sentence']
    subreddit= form_data['subreddit']
    model= form_data['model']
    if(model=="ULMFit"):
        learn= ufmodels[subreddit]
        prediction = learn.predict(sentence, 10, temperature=0.10)
        return JSONResponse({'result': str(prediction)})
    elif(model=="GPT-2"):
        model_output_path= str(path)+"/"+subreddit[2:]+"_100000/"
        config = {
                'model_type': 'gpt2',
                'model_name_or_path': model_output_path,
                }
        sys.argv = ['foo']
        prompts=[sentence]
        sentences = main(config, prompts)
        return JSONResponse({'result': str(sentences[0])})


if __name__ == '__main__':
    if 'serve' in sys.argv:
        uvicorn.run(app=app, host='0.0.0.0', port=5000, log_level="info")
