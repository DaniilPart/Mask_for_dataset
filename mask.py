#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from typing import List, Optional

IMG_EXT = ('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff')


class OverlayApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Interactive Mask Overlay and Segmentation Editor")
        self.geometry("1200x800")

        self.bg_files: List[str] = []
        self.ov_files: List[str] = []
        self.seg_dir: Optional[str] = None
        self.current_seg_path: Optional[str] = None
        self.bg_idx = self.ov_idx = 0

        self.scale = 1.0
        self.ov_pos = (0, 0)
        self.bg_img: Optional[Image.Image] = None
        self.ov_img: Optional[Image.Image] = None
        self.ov_img_orig: Optional[Image.Image] = None

        bar = tk.Frame(self)
        bar.pack(fill="x", padx=4, pady=4)

        tk.Button(bar, text="Background Folder…", command=self.choose_bg_dir).pack(side="left")
        tk.Button(bar, text="Mask Folder…", command=self.choose_ov_dir).pack(side="left")
        tk.Button(bar, text="Segmentation Folder…", command=self.choose_seg_dir).pack(side="left")

        tk.Button(bar, text="← Background", command=lambda: self.shift_bg(-1)).pack(side="left", padx=(10, 0))
        tk.Button(bar, text="Background →", command=lambda: self.shift_bg(1)).pack(side="left")
        tk.Button(bar, text="← Mask", command=lambda: self.shift_ov(-1)).pack(side="left", padx=(10, 0))
        tk.Button(bar, text="Mask →", command=lambda: self.shift_ov(1)).pack(side="left")

        self.save_button = tk.Button(bar, text="Save Result and Segmentation", command=self.save_all)
        self.save_button.pack(side="right", padx=10)

        self.canvas = tk.Canvas(self, bg="grey")
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<MouseWheel>", self.on_wheel)
        self.canvas.bind("<Button-4>", self.on_wheel)
        self.canvas.bind("<Button-5>", self.on_wheel)

    def choose_bg_dir(self):
        path = filedialog.askdirectory(title="Select Background Folder")
        if path:
            self.bg_files = self.scan_dir(path)
            self.bg_idx = 0
            self.update_view()

    def choose_ov_dir(self):
        path = filedialog.askdirectory(title="Select Mask Folder (transparent background)")
        if path:
            self.ov_files = self.scan_dir(path)
            self.ov_idx = 0
            self.update_view()

    def choose_seg_dir(self):
        path = filedialog.askdirectory(title="Select Segmentation Files Folder")
        if path:
            self.seg_dir = path
            self.update_view()

    @staticmethod
    def scan_dir(folder: str) -> List[str]:
        return sorted([os.path.join(folder, f) for f in os.listdir(folder)
                       if f.lower().endswith(IMG_EXT)])

    def find_segmentation_for_current_background(self) -> Optional[str]:
        if not self.seg_dir or not self.bg_files:
            return None

        # Получаем имя файла фона, например 'IMG_8644.PNG'
        bg_path = self.bg_files[self.bg_idx]
        bg_name = os.path.basename(bg_path)

        # Отделяем имя от расширения, например 'IMG_8644' и '.PNG'
        bg_base, bg_ext = os.path.splitext(bg_name)

        # Разбиваем имя на части по символу '_', например ['IMG', '8644']
        parts = bg_base.split('_')

        # Проверяем, что имя состоит из двух частей (префикс и номер)
        if len(parts) != 2:
            return None

        # Собираем новое имя для маски по вашей схеме
        # Например, 'IMG' + '_road_' + '8644' + '.png'
        # Расширение .png задано явно, чтобы избежать проблем с регистром
        mask_name = f"{parts[0]}_road_{parts[1]}.png"

        # Создаем полный путь к файлу маски
        mask_path = os.path.join(self.seg_dir, mask_name)

        # Проверяем, существует ли такой файл, и возвращаем путь если да
        if os.path.exists(mask_path):
            return mask_path

        # Если файл не найден, возвращаем None
        return None

    def shift_bg(self, step: int):
        if self.bg_files:
            self.bg_idx = (self.bg_idx + step) % len(self.bg_files)
            self.update_view()

    def shift_ov(self, step: int):
        if self.ov_files:
            self.ov_idx = (self.ov_idx + step) % len(self.ov_files)
            self.update_view()

    def on_click(self, ev):
        self.ov_pos = (ev.x, ev.y)
        self.redraw_overlay()

    def on_wheel(self, ev):
        direction = +1 if (ev.delta > 0 or ev.num == 4) else -1
        self.scale *= 1.1 if direction > 0 else 0.9
        self.scale = max(0.1, min(self.scale, 5.0))
        self.redraw_overlay()

    def update_view(self):
        if not (self.bg_files and self.ov_files):
            return

        self.bg_img = Image.open(self.bg_files[self.bg_idx]).convert("RGBA")
        self.tk_bg = ImageTk.PhotoImage(self.bg_img)

        self.ov_img_orig = Image.open(self.ov_files[self.ov_idx]).convert("RGBA")
        self.scale = 1.0
        self.ov_pos = (self.bg_img.width // 2, self.bg_img.height // 2)

        self.current_seg_path = self.find_segmentation_for_current_background()
        if self.current_seg_path:
            self.title(f"Editor - Segmentation found: {os.path.basename(self.current_seg_path)}")
        else:
            self.title(
                f"Editor - WARNING: Segmentation for background ({os.path.basename(self.bg_files[self.bg_idx])}) NOT FOUND")

        self.canvas.delete("all")
        self.canvas.config(width=self.tk_bg.width(), height=self.tk_bg.height())
        self.canvas.create_image(0, 0, image=self.tk_bg, anchor="nw")
        self.redraw_overlay()

    def redraw_overlay(self):
        if not self.ov_img_orig:
            return

        w, h = self.ov_img_orig.size
        new_size = (int(w * self.scale), int(h * self.scale))
        self.ov_img = self.ov_img_orig.resize(new_size, Image.LANCZOS)
        self.tk_ov = ImageTk.PhotoImage(self.ov_img)

        if self.canvas.find_withtag("ov"):
            self.canvas.itemconfigure("ov", image=self.tk_ov)
            self.canvas.coords("ov", self.ov_pos)
        else:
            self.canvas.create_image(*self.ov_pos, image=self.tk_ov, anchor="center", tags="ov")

    def save_all(self):
        if not (self.bg_img and self.ov_img):
            messagebox.showwarning("No Data", "Background or mask not selected.")
            return

        visual_result = self.bg_img.copy()
        top_left_x = self.ov_pos[0] - self.ov_img.width // 2
        top_left_y = self.ov_pos[1] - self.ov_img.height // 2
        visual_result.paste(self.ov_img, (top_left_x, top_left_y), self.ov_img)

        save_path_visual = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png")],
            title="Save visual result as...")

        if not save_path_visual:
            messagebox.showinfo("Cancelled", "Saving cancelled.")
            return

        visual_result.save(save_path_visual)

        if not self.current_seg_path:
            messagebox.showerror("Error", "Segmentation file not found for this background. Segmentation not changed.")
            return

        try:
            seg_img_original = Image.open(self.current_seg_path)
            seg_img_copy = seg_img_original.copy()
            if seg_img_copy.mode != 'RGB':
                seg_img_copy = seg_img_copy.convert('RGB')

            red_fill = Image.new("RGB", self.ov_img.size, (255, 0, 0))
            seg_img_copy.paste(red_fill, (top_left_x, top_left_y), mask=self.ov_img)

            visual_dir, visual_basename = os.path.split(save_path_visual)
            visual_name_no_ext, visual_ext = os.path.splitext(visual_basename)
            new_mask_name = f"{visual_name_no_ext}_road_{visual_ext}"

            save_path_mask = filedialog.asksaveasfilename(
                initialdir=visual_dir,
                initialfile=new_mask_name,
                defaultextension=".png",
                filetypes=[("PNG", "*.png")],
                title="Save new mask as...")

            if not save_path_mask:
                messagebox.showinfo("Cancelled", "Saving new mask cancelled. Visual result was saved.")
                return

            seg_img_copy.save(save_path_mask)

            messagebox.showinfo("Success!",
                                f"Visual result saved to:\n{save_path_visual}\n\n"
                                f"New mask saved to:\n{save_path_mask}")

        except Exception as e:
            messagebox.showerror("Segmentation Save Error", f"An error occurred:\n{e}")


if __name__ == "__main__":
    app = OverlayApp()
    app.mainloop()
