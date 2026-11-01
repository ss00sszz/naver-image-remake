import io, zipfile, random
import streamlit as st
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

st.set_page_config(page_title='네이버 이미지 리메이커', page_icon='🖼️')
st.title('네이버 이미지 리메이커')
st.info('1단계 버전: Windows 보조 프로그램에서 추출한 ZIP 파일을 올려 이미지를 가공합니다. 웹사이트에서 PC 크롬을 직접 실행하지 않습니다.')
files=st.file_uploader('사진 또는 Windows 보조 프로그램이 만든 ZIP 업로드',type=['png','jpg','jpeg','webp','zip'],accept_multiple_files=True)
style=st.selectbox('필터', ['액자 + 그림자 + 랜덤 기울기','액자','원본 비율 유지'])
angle=st.slider('최대 기울기(도)',0,15,5)
size=st.selectbox('정사각형 출력 크기',[900,1080])
seed=st.number_input('랜덤 시드',0,999999,42)

def transform(data,idx):
    im=Image.open(io.BytesIO(data)).convert('RGB')
    im.thumbnail((size-110,size-160))
    if style=='원본 비율 유지':return im
    pad=22
    base=Image.new('RGBA',(im.width+pad*2,im.height+pad*2+28),'white')
    base.paste(im,(pad,pad))
    if style=='액자':return base
    rng=random.Random(seed+idx)
    rotated=base.rotate(rng.uniform(-angle,angle),resample=Image.Resampling.BICUBIC,expand=True)
    shadow=Image.new('RGBA',(rotated.width+40,rotated.height+40),(0,0,0,0))
    mask=rotated.getchannel('A').filter(ImageFilter.GaussianBlur(12))
    shade=Image.new('RGBA',rotated.size,(0,0,0,80))
    shadow.paste(shade,(22,22),mask)
    shadow.alpha_composite(rotated,(10,10))
    return shadow

if files and st.button('이미지 가공 및 ZIP 만들기',type='primary'):
    output=io.BytesIO(); n=0; previews=[]; errors=[]
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as out:
        for uploaded in files:
            sources=[]
            raw=uploaded.getvalue()
            if uploaded.name.lower().endswith('.zip'):
                try:
                    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                        for entry in archive.infolist():
                            if not entry.is_dir() and entry.filename.lower().endswith(('.png','.jpg','.jpeg','.webp')) and entry.file_size <= 20_000_000:
                                sources.append((entry.filename,archive.read(entry)))
                except Exception as exc:errors.append(f'{uploaded.name}: {exc}')
            else:sources.append((uploaded.name,raw))
            for name,data in sources[:100]:
                try:
                    img=transform(data,n); buf=io.BytesIO();img.save(buf,format='PNG')
                    n+=1;out.writestr(f'edited_{n:03d}.png',buf.getvalue())
                    if len(previews)<4:previews.append(img)
                except Exception as exc:errors.append(f'{name}: {exc}')
    if n:
        st.success(f'{n}장 가공 완료')
        st.image(previews,width=180)
        st.download_button('가공 이미지 ZIP 다운로드',output.getvalue(),file_name='remade_images.zip',mime='application/zip')
    for e in errors[:10]:st.warning(e)
