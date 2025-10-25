#!/usr/bin/env python3
import os, io, random, argparse
from typing import List
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import cv2
import img2pdf
from pdf2image import convert_from_path
from PyPDF2 import PdfReader, PdfWriter

# ---------- حذف صفحات ----------
def remove_pages(input_pdf: str, pages_to_remove: List[int], output_pdf: str):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    total = len(reader.pages)
    remove_set = set([p-1 for p in pages_to_remove if 1 <= p <= total])  # 0-based
    for i in range(total):
        if i in remove_set:
            continue
        writer.add_page(reader.pages[i])
    with open(output_pdf, "wb") as f:
        writer.write(f)

# ---------- افکت‌های شبیه اسکن ----------
def random_contrast_brightness(img: Image.Image) -> Image.Image:
    enhancer_c = ImageEnhance.Contrast(img)
    enhancer_b = ImageEnhance.Brightness(img)
    c = random.uniform(0.9, 1.6)
    b = random.uniform(0.9, 1.15)
    img = enhancer_c.enhance(c)
    img = enhancer_b.enhance(b)
    return img

def add_paper_texture(img: Image.Image) -> Image.Image:
    w, h = img.size
    noise = np.random.normal(loc=0, scale=8, size=(h, w)).astype(np.uint8)
    if img.mode != "RGB":
        base = img.convert("RGB")
    else:
        base = img.copy()
    base_np = np.array(base).astype(np.int16)
    tex_np = noise.astype(np.int16)
    alpha = 0.08 + random.random()*0.12
    for c in range(3):
        base_np[:,:,c] = base_np[:,:,c] - (tex_np * alpha)
    base_np = np.clip(base_np, 0, 255).astype(np.uint8)
    return Image.fromarray(base_np)

def add_gaussian_film_grain(img: Image.Image) -> Image.Image:
    w, h = img.size
    arr = np.array(img).astype(np.int16)
    noise = np.random.normal(0, 6, (h, w, 1))
    arr = arr + noise
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)

def random_skew_and_rotate(img: Image.Image) -> Image.Image:
    w, h = img.size
    img = img.rotate(random.uniform(-2.5, 2.5), resample=Image.BICUBIC, expand=True, fillcolor=(255,255,255))
    arr = np.array(img)
    h2, w2 = arr.shape[0], arr.shape[1]
    src = np.float32([[0,0],[w2-1,0],[w2-1,h2-1],[0,h2-1]])
    max_shift_x = w2 * 0.03
    max_shift_y = h2 * 0.03
    dst = src + np.float32([
        [random.uniform(-max_shift_x, max_shift_x), random.uniform(-max_shift_y, max_shift_y)],
        [random.uniform(-max_shift_x, max_shift_x), random.uniform(-max_shift_y, max_shift_y)],
        [random.uniform(-max_shift_x, max_shift_x), random.uniform(-max_shift_y, max_shift_y)],
        [random.uniform(-max_shift_x, max_shift_x), random.uniform(-max_shift_y, max_shift_y)],
    ])
    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(arr, M, (w2, h2), borderValue=(255,255,255))
    return Image.fromarray(warped)

def add_vignette(img: Image.Image) -> Image.Image:
    w,h = img.size
    x = np.linspace(-1,1,w)
    y = np.linspace(-1,1,h)
    xv, yv = np.meshgrid(x,y)
    dr = np.sqrt(xv**2 + yv**2)
    vign = (1 - np.clip((dr - 0.5) / 0.7, 0, 1))
    arr = np.array(img).astype(np.float32)
    if arr.ndim == 2:
        arr = np.stack([arr,arr,arr], axis=2)
    for c in range(3):
        arr[:,:,c] = arr[:,:,c] * vign
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)

def make_page_look_scanned(pil_img: Image.Image) -> Image.Image:
    img = pil_img.convert("RGB")
    img = random_contrast_brightness(img)
    img = add_gaussian_film_grain(img)
    if random.random() < 0.8:
        img = add_paper_texture(img)
    img = random_skew_and_rotate(img)
    img = add_vignette(img)
    if random.random() < 0.6:
        img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.2,0.9)))
    return img

# ---------- تبدیل متن-PDF → PDF تصویری ----------
def pdf_text_to_scanned_pdf(input_pdf: str, output_pdf: str, poppler_path: str=None, dpi:int=200):
    pages = convert_from_path(input_pdf, dpi=dpi, poppler_path=poppler_path)
    processed = []
    for i, pg in enumerate(pages):
        scanned = make_page_look_scanned(pg)
        processed.append(scanned)

    # ذخیره به PDF از تصاویر (کیفیت مناسب)
    image_bytes = []
    for img in processed:
        bio = io.BytesIO()
        img.save(bio, format="JPEG", quality=90)
        image_bytes.append(bio.getvalue())
    with open(output_pdf, "wb") as f:
        f.write(img2pdf.convert(image_bytes))

# ---------- ابزار پارس صفحات ----------
def parse_page_list(s: str, maxpage:int=None) -> List[int]:
    if not s:
        return []
    parts = s.split(",")
    res = []
    for p in parts:
        p = p.strip()
        if "-" in p:
            a,b = p.split("-")
            a=int(a); b=int(b)
            res.extend(list(range(a, b+1)))
        else:
            res.append(int(p))
    res = sorted(set(res))
    if maxpage:
        res = [x for x in res if 1 <= x <= maxpage]
    return res

# اجرای خط‌فرمان (اختیاری)
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--remove", "-r", help="مثل: 1,3,5-7", default=None)
    parser.add_argument("--in", dest="input_pdf", required=True)
    parser.add_argument("--out", dest="output_pdf", required=True)
    parser.add_argument("--scan", action="store_true")
    parser.add_argument("--poppler-path", default=None)
    parser.add_argument("--dpi", type=int, default=200)
    args = parser.parse_args()

    work_input = args.input_pdf
    if args.remove:
        reader = PdfReader(work_input)
        total = len(reader.pages)
        pages_to_remove = parse_page_list(args.remove, maxpage=total)
        if pages_to_remove:
            tmp_removed = args.output_pdf + ".tmp_removed.pdf"
            remove_pages(work_input, pages_to_remove, tmp_removed)
            work_input = tmp_removed

    if args.scan:
        pdf_text_to_scanned_pdf(work_input, args.output_pdf, poppler_path=args.poppler_path, dpi=args.dpi)
    else:
        if args.remove:
            os.replace(work_input, args.output_pdf)
        else:
            print("گزینه‌ای وارد نکردی؛ --remove یا --scan بده.")
