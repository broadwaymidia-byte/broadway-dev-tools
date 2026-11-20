from pathlib import Path

from PIL import Image, ImageDraw


pasta = Path(__file__).resolve().parent
cenas = pasta / "cenas"
logos = pasta / "logos" / "cafe-aurora"
cenas.mkdir(exist_ok=True)
logos.mkdir(parents=True, exist_ok=True)

for indice, cor in enumerate(("#395E55", "#784F3E", "#593D51"), 1):
    imagem = Image.new("RGB", (1080, 1920), cor)
    desenho = ImageDraw.Draw(imagem)
    deslocamento = (indice - 2) * 115
    desenho.ellipse((180 + deslocamento, 370, 900 + deslocamento, 1090), fill="#ECD7B7")
    desenho.ellipse((260 + deslocamento, 450, 820 + deslocamento, 1010), fill="#915239")
    desenho.ellipse((330 + deslocamento, 520, 750 + deslocamento, 940), outline="#E1AC7B", width=20)
    imagem.save(cenas / f"cena-{indice}.png")

logo = Image.new("RGBA", (144, 144))
desenho = ImageDraw.Draw(logo)
desenho.ellipse((4, 4, 140, 140), fill="#FFD39D")
desenho.line([(42, 101), (72, 43), (102, 101)], fill="#172E2B", width=9)
desenho.line([(56, 78), (88, 78)], fill="#172E2B", width=9)
logo.save(logos / "logo.png")
