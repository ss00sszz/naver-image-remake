import io, zipfile, random, os
import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter

st.set_page_config(page_title='네이버 이미지 리메이커 v2', page_icon='🖼️', layout='wide')
st.title('🖼️ 네이버 이미지 리메이커 v2')
st.info('Windows 보조 프로그램으로 수집한 ZIP 또는 직접 선택한 이미지를 업로드하세요. 클라우드에서 PC 크롬을 직접 실행하지는 않습니다.')
files = st.file_uploader('사진 또는 ZIP 업로드', type=['png','jpg','jpeg','webp','zip'], accept_multiple_files=True)
left,right=st.columns(2)
with left:
    st.subheader('액자 설정')
    style=st.selectbox('효과', ['액자 + 그림자 + 랜덤 기울기','액자만','필터만 (액자 없음)'])
    preset=st.selectbox('액자 색상', ['흰색','검정','베이지','아이보리','연핑크','하늘색','연두색','회색','직접 지정'])
    colors={'흰색':'#FFFFFF','검정':'#111111','베이지':'#E8D9C5','아이보리':'#FFF8E7','연핑크':'#F6CED8','하늘색':'#CDE9F8','연두색':'#DCEAC8','회색':'#D3D3D3'}
    frame_color=st.color_picker('액자 색상 직접 선택',value=colors.get(preset,'#FFFFFF')) if preset=='직접 지정' else colors[preset]
    frame_width=st.slider('액자 두께 (px)',0,100,24)
    angle=st.slider('랜덤 기울기 범위 (±도)',0,20,5)
    shadow_strength=st.slider('그림자 강도',0,100,45)
with right:
    st.subheader('밝기 · 색감 직접 조정')
    brightness=st.slider('밝기',50,200,100,5,help='100이 원본입니다.')
    saturation=st.slider('채도',0,200,100,5,help='0은 흑백, 100은 원본입니다.')
    contrast=st.slider('대비',50,200,100,5)
    sharpness=st.slider('선명도',0,200,100,5)
    size=st.selectbox('최대 출력 크기', [900,1080,1440,2048])
    seed=st.number_input('랜덤 시드',0,999999,42)

def transform(data, idx):
    with Image.open(io.BytesIO(data)) as source:
        im=source.convert('RGB')
    im=ImageEnhance.Brightness(im).enhance(brightness/100)
    im=ImageEnhance.Color(im).enhance(saturation/100)
    im=ImageEnhance.Contrast(im).enhance(contrast/100)
    im=ImageEnhance.Sharpness(im).enhance(sharpness/100)
    reserve=frame_width*2+100 if style!='필터만 (액자 없음)' else 0
    im.thumbnail((max(100,size-reserve),max(100,size-reserve)),Image.Resampling.LANCZOS)
    if style=='필터만 (액자 없음)': return im
    base=Image.new('RGBA',(im.width+frame_width*2,im.height+frame_width*2+int(frame_width*.7)),frame_color)
    base.paste(im,(frame_width,frame_width))
    if style=='액자만':return base
    rng=random.Random(seed+idx)
    rotated=base.rotate(rng.uniform(-angle,angle),resample=Image.Resampling.BICUBIC,expand=True)
    margin=45
    canvas=Image.new('RGBA',(rotated.width+margin*2,rotated.height+margin*2),(0,0,0,0))
    if shadow_strength:
        alpha=rotated.getchannel('A').filter(ImageFilter.GaussianBlur(13))
        shadow=Image.new('RGBA',rotated.size,(0,0,0,int(shadow_strength*1.8)))
        shadow.putalpha(alpha.point(lambda a:int(a*shadow_strength*1.8/255)))
        canvas.alpha_composite(shadow,(margin+12,margin+14))
    canvas.alpha_composite(rotated,(margin,margin))
    return canvas

def sources_from_upload(uploaded):
    raw=uploaded.getvalue()
    if not uploaded.name.lower().endswith('.zip'):
        yield uploaded.name,raw
        return
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        count=0
        for item in archive.infolist():
            if count>=100:break
            if item.is_dir() or item.file_size>20_000_000 or not item.filename.lower().endswith(('.png','.jpg','.jpeg','.webp')):continue
            yield item.filename,archive.read(item)
            count+=1

if files:
    try:
        first=next(sources_from_upload(files[0]))
        st.subheader('미리보기 (첫 번째 이미지)')
        st.image(transform(first[1],0),caption='현재 슬라이더 설정 적용',width=340)
    except Exception as exc:st.warning(f'미리보기를 생성하지 못했습니다: {exc}')

if files and st.button('이미지 가공 및 ZIP 만들기',type='primary'):
    output=io.BytesIO();n=0;errors=[]
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as out:
        for uploaded in files:
            try:
                for name,data in sources_from_upload(uploaded):
                    try:
                        im=transform(data,n);buf=io.BytesIO();im.save(buf,format='PNG')
                        n+=1;out.writestr(f'edited_{n:03d}.png',buf.getvalue())
                    except Exception as exc:errors.append(f'{name}: {exc}')
            except Exception as exc:errors.append(f'{uploaded.name}: {exc}')
    if n:
        st.success(f'{n}장 가공 완료')
        st.download_button('가공 이미지 ZIP 다운로드',output.getvalue(),file_name='remade_images.zip',mime='application/zip')
    for err in errors[:10]:st.warning(err)
