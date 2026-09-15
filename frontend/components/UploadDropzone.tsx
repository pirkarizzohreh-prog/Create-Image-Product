"use client";

import { ChangeEvent, DragEvent, useRef, useState } from "react";

interface Props {
  files: File[];
  onChange: (files: File[]) => void;
}

export default function UploadDropzone({ files, onChange }: Props) {
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function addFiles(list: FileList | null) {
    if (!list) return;
    const incoming = Array.from(list).filter((f) => f.type.startsWith("image/"));
    onChange([...files, ...incoming]);
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragOver(false);
    addFiles(e.dataTransfer.files);
  }

  function removeAt(idx: number) {
    onChange(files.filter((_, i) => i !== idx));
  }

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors ${
          dragOver ? "border-brand-500 bg-brand-50" : "border-slate-300 bg-white hover:bg-slate-50"
        }`}
      >
        <p className="text-sm font-medium text-slate-700">Drag & drop product photos here</p>
        <p className="mt-1 text-xs text-slate-500">or click to browse — JPEG, PNG, WebP, HEIC. Bulk upload supported.</p>
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          multiple
          className="hidden"
          onChange={(e: ChangeEvent<HTMLInputElement>) => addFiles(e.target.files)}
        />
      </div>

      {files.length > 0 && (
        <ul className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {files.map((f, i) => (
            <li key={`${f.name}-${i}`} className="relative overflow-hidden rounded-md border border-slate-200">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={URL.createObjectURL(f)} alt={f.name} className="h-24 w-full object-cover" />
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  removeAt(i);
                }}
                className="absolute right-1 top-1 rounded-full bg-black/60 px-1.5 text-xs text-white hover:bg-black/80"
              >
                ✕
              </button>
              <p className="truncate bg-white px-1.5 py-0.5 text-[10px] text-slate-500">{f.name}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
