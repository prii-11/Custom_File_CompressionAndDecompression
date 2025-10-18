import customtkinter as ctk
import tkinter.filedialog as filedialog
from tkinter import messagebox
import os
import io
import zipfile
from PIL import Image, ImageTk
from tempfile import TemporaryDirectory
import fitz  
import subprocess
import threading
import random
import platform

# Optional: only import winsound on Windows
if platform.system() == "Windows":
    import winsound


class SmartFileCompressorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart File Compressor")
        self.root.geometry("800x500")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.file_path = None
        self.file_type = ctk.StringVar(value="docx")
        self.compressed_data = None
        self.temp_video_path = None
        self.temp_dir = None

        self.bg_canvas = ctk.CTkCanvas(self.root, width=800, height=500, bg="#111111", highlightthickness=0)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        self.floating_circles = []
        self.setup_floating_background()
        self.animate_floating_circles()

        self.setup_ui()

  
    def setup_floating_background(self):
        for _ in range(20):
            x = random.randint(0, 800)
            y = random.randint(0, 500)
            size = random.randint(20, 60)
            speed = random.uniform(0.5, 1.5)
            circle = self.bg_canvas.create_oval(x, y, x + size, y + size, fill="#1f1f1f", outline="")
            self.floating_circles.append({'id': circle, 'x': x, 'y': y, 'size': size, 'speed': speed})

    def animate_floating_circles(self):
        for circle in self.floating_circles:
            circle['y'] -= circle['speed']
            if circle['y'] + circle['size'] < 0:
                circle['y'] = 500
                circle['x'] = random.randint(0, 800)
            self.bg_canvas.coords(circle['id'], circle['x'], circle['y'],
                                  circle['x'] + circle['size'], circle['y'] + circle['size'])
        self.root.after(50, self.animate_floating_circles)

    def setup_ui(self):
        ctk.CTkLabel(self.root, text="Smart File Compression Tool",
                     font=ctk.CTkFont(size=26, weight="bold"), text_color="white").place(relx=0.5, rely=0.07, anchor='center')

        dropdown_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        dropdown_frame.place(relx=0.5, rely=0.17, anchor='center')
        ctk.CTkLabel(dropdown_frame, text="Select File Type: ").pack(side="left", padx=10)
        self.file_type_menu = ctk.CTkOptionMenu(dropdown_frame, values=["docx", "jpg", "pdf", "mp4"], variable=self.file_type)
        self.file_type_menu.pack(side="left")

        self.select_btn = ctk.CTkButton(self.root, text="Choose File", command=self.select_file)
        self.select_btn.place(relx=0.5, rely=0.27, anchor='center')

        self.file_label = ctk.CTkLabel(self.root, text="No file selected", text_color="gray")
        self.file_label.place(relx=0.5, rely=0.33, anchor='center')

        self.image_preview = ctk.CTkLabel(self.root, text="")
        self.image_preview.place(relx=0.5, rely=0.42, anchor='center')

        self.progress_bar = ctk.CTkProgressBar(self.root, width=400)
        self.progress_bar.set(0)
        self.progress_bar.place(relx=0.5, rely=0.5, anchor='center')

        self.compress_btn = ctk.CTkButton(self.root, text="Compress File", command=self.start_compression, state="disabled")
        self.compress_btn.place(relx=0.5, rely=0.57, anchor='center')

        self.save_btn = ctk.CTkButton(self.root, text="Save Compressed File", command=self.save_file, state="disabled")
        self.save_btn.place(relx=0.5, rely=0.64, anchor='center')

        self.status_label = ctk.CTkLabel(self.root, text="")
        self.status_label.place(relx=0.5, rely=0.72, anchor='center')

        self.stats_label = ctk.CTkLabel(self.root, text="")
        self.stats_label.place(relx=0.5, rely=0.77, anchor='center')

  
    def select_file(self):
        filetypes = {
            'docx': [('DOCX files', '*.docx')],
            'jpg': [('JPEG files', '*.jpg')],
            'pdf': [('PDF files', '*.pdf')],
            'mp4': [('Video files', '*.mp4')]
        }
        ext = self.file_type.get()
        file = filedialog.askopenfilename(filetypes=filetypes.get(ext, [('All files', '*.*')]))
        if file:
            self.file_path = file
            self.file_label.configure(text=f"Selected: {os.path.basename(file)}")
            self.compress_btn.configure(state="normal")
            self.status_label.configure(text="")
            self.stats_label.configure(text="")
            self.image_preview.configure(image=None, text="")

            if ext == 'jpg':
                try:
                    img = Image.open(file)
                    img.thumbnail((200, 200))
                    img = ImageTk.PhotoImage(img)
                    self.image_preview.configure(image=img)
                    self.image_preview.image = img
                except:
                    pass

    def start_compression(self):
        threading.Thread(target=self.compress_file).start()

    def compress_file(self):
        if not self.file_path:
            return

        self.progress_bar.set(0.2)
        ext = self.file_type.get()
        try:
            orig_size = os.path.getsize(self.file_path)

            if ext == 'docx':
                self.compressed_data = self.compress_docx(self.file_path)
                self.temp_video_path = None
                self.cleanup_temp()
                msg = "Compressed DOCX by recompressing embedded images."
            elif ext == 'jpg':
                img = Image.open(self.file_path)
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=30, optimize=True, progressive=True)
                self.compressed_data = output.getvalue()
                self.temp_video_path = None
                self.cleanup_temp()
                msg = "Compressed JPG with reduced quality."
            elif ext == 'pdf':
                self.compressed_data = self.compress_pdf(self.file_path)
                self.temp_video_path = None
                self.cleanup_temp()
                msg = "Compressed PDF including embedded images."
            elif ext == 'mp4':
                self.cleanup_temp()
                self.temp_video_path = self.compress_video_ffmpeg(self.file_path)
                self.compressed_data = None
                msg = "Compressed video using FFmpeg."
            else:
                raise Exception("Unsupported file type")

            self.progress_bar.set(1)
            self.status_label.configure(text=msg)
            self.save_btn.configure(state="normal")

            new_size = os.path.getsize(self.temp_video_path) if self.temp_video_path else len(self.compressed_data)
            savings = round((orig_size - new_size) / orig_size * 100, 2)
            self.stats_label.configure(
                text=f"Original: {round(orig_size/1024, 2)} KB | Compressed: {round(new_size/1024, 2)} KB | Saved: {savings}%"
            )

            if platform.system() == "Windows":
                winsound.MessageBeep()
            messagebox.showinfo("Done", msg)

        except Exception as e:
            self.progress_bar.set(0)
            messagebox.showerror("Error", str(e))

  
    def compress_docx(self, input_path, quality=40):
        with TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(input_path, 'r') as zin:
                zin.extractall(tmpdir)

            media_folder = os.path.join(tmpdir, 'word', 'media')
            if os.path.exists(media_folder):
                for file in os.listdir(media_folder):
                    img_path = os.path.join(media_folder, file)
                    try:
                        img = Image.open(img_path)
                        if img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")
                        img.save(img_path, format='JPEG', quality=quality, optimize=True)
                    except:
                        pass

            compressed_docx_path = os.path.join(tmpdir, "compressed.docx")
            with zipfile.ZipFile(compressed_docx_path, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
                for folder, _, files in os.walk(tmpdir):
                    for file in files:
                        full_path = os.path.join(folder, file)
                        arcname = os.path.relpath(full_path, tmpdir)
                        if arcname != "compressed.docx":
                            zout.write(full_path, arcname)

            with open(compressed_docx_path, 'rb') as f:
                return f.read()

    def compress_pdf(self, input_path):
        output = io.BytesIO()
        doc = fitz.open(input_path)

        for page_index in range(len(doc)):
            page = doc[page_index]
            images = page.get_images(full=True)
            for img in images:
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                try:
                    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
                    img_io = io.BytesIO()
                    image.save(img_io, format="JPEG", quality=40, optimize=True)
                    doc.update_image(xref, img_io.getvalue())
                except Exception:
                    continue

        doc.save(output, garbage=4, deflate=True, clean=True)
        doc.close()
        return output.getvalue()

    def compress_video_ffmpeg(self, input_path):
        base, ext = os.path.splitext(os.path.basename(input_path))
        self.temp_dir = TemporaryDirectory()
        output_path = os.path.join(self.temp_dir.name, base + "_compressed" + ext)

        command = [
            'ffmpeg',
            '-i', input_path,
            '-vcodec', 'libx264',
            '-crf', '28',
            '-preset', 'fast',
            '-acodec', 'aac',
            '-b:a', '128k',
            output_path
        ]

        subprocess.run(command, check=True)
        return output_path

    def save_file(self):
        ext = self.file_type.get()
        extensions = {'docx': '.docx', 'jpg': '.jpg', 'pdf': '.pdf', 'mp4': '.mp4'}
        save_path = filedialog.asksaveasfilename(defaultextension=extensions[ext])

        if save_path:
            if ext == 'mp4' and self.temp_video_path:
                with open(self.temp_video_path, 'rb') as src, open(save_path, 'wb') as dest:
                    dest.write(src.read())
                self.cleanup_temp()
            else:
                with open(save_path, 'wb') as f:
                    f.write(self.compressed_data)
            messagebox.showinfo("Saved", f"Compressed file saved as: {save_path}")

    def cleanup_temp(self):
        if self.temp_dir:
            self.temp_dir.cleanup()
            self.temp_dir = None


if __name__ == "__main__":
    root = ctk.CTk()
    app = SmartFileCompressorApp(root)
    root.mainloop()
