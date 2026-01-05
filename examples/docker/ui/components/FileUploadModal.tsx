'use client';

import { useState, useRef, useCallback } from 'react';
import {
  X,
  Upload,
  File,
  Trash2,
  FolderOpen,
  Loader2,
  CheckCircle,
  AlertCircle,
} from 'lucide-react';

interface FileUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId: string;
  apiKey: string;
  apiUrl?: string;
  onUploadComplete?: (files: string[]) => void;
}

export function FileUploadModal({
  isOpen,
  onClose,
  sessionId,
  apiKey,
  apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  onUploadComplete,
}: FileUploadModalProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [targetPath, setTargetPath] = useState('/workspace');
  const [overwrite, setOverwrite] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const totalSize = files.reduce((acc, f) => acc + f.size, 0);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    setFiles(prev => [...prev, ...selectedFiles]);
    setUploadStatus('idle');
    setErrorMessage('');
  }, []);

  const handleRemoveFile = useCallback((index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const droppedFiles = Array.from(e.dataTransfer.files);
    setFiles(prev => [...prev, ...droppedFiles]);
    setUploadStatus('idle');
    setErrorMessage('');
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
  }, []);

  const handleUpload = async () => {
    if (files.length === 0) return;

    setIsUploading(true);
    setUploadStatus('idle');
    setErrorMessage('');

    try {
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
      });

      // Build URL with path as query parameter
      const uploadUrl = new URL(`${apiUrl}/api/files/${sessionId}/upload`);
      if (targetPath && targetPath !== '/workspace') {
        uploadUrl.searchParams.set('path', targetPath.replace(/^\/workspace\/?/, ''));
      }

      const response = await fetch(uploadUrl.toString(), {
        method: 'POST',
        headers: {
          'X-API-Key': apiKey,
        },
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
      }

      const result = await response.json();
      setUploadedFiles(result.uploaded_files || []);
      setUploadStatus('success');
      setFiles([]);
      onUploadComplete?.(result.uploaded_files || []);
    } catch (error) {
      setUploadStatus('error');
      setErrorMessage(error instanceof Error ? error.message : 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleClose = () => {
    setFiles([]);
    setUploadStatus('idle');
    setErrorMessage('');
    setUploadedFiles([]);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-lg shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <div className="flex items-center gap-2">
            <Upload className="w-5 h-5 text-blue-400" />
            <h2 className="text-lg font-semibold text-white">Upload Files</h2>
          </div>
          <button
            onClick={handleClose}
            className="p-1 hover:bg-gray-800 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          {/* Drop Zone */}
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-gray-600 rounded-lg p-8 text-center cursor-pointer hover:border-blue-500 hover:bg-blue-500/5 transition-colors"
          >
            <Upload className="w-10 h-10 text-gray-500 mx-auto mb-3" />
            <p className="text-sm text-gray-400">
              Drag & drop files here or click to browse
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Max 50MB per file, 200MB total
            </p>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>

          {/* Target Path */}
          <div>
            <label className="block text-sm text-gray-400 mb-1">
              <FolderOpen className="w-4 h-4 inline mr-1" />
              Target Path
            </label>
            <input
              type="text"
              value={targetPath}
              onChange={(e) => setTargetPath(e.target.value)}
              className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
              placeholder="/workspace"
            />
          </div>

          {/* Overwrite Option */}
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={overwrite}
              onChange={(e) => setOverwrite(e.target.checked)}
              className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-blue-500 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-400">Overwrite existing files</span>
          </label>

          {/* File List */}
          {files.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm text-gray-400">
                <span>{files.length} file(s) selected</span>
                <span>{formatFileSize(totalSize)} total</span>
              </div>
              <div className="max-h-40 overflow-y-auto space-y-1">
                {files.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between bg-gray-800/50 rounded-lg px-3 py-2"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <File className="w-4 h-4 text-gray-400 flex-shrink-0" />
                      <span className="text-sm text-gray-300 truncate">
                        {file.name}
                      </span>
                      <span className="text-xs text-gray-500 flex-shrink-0">
                        {formatFileSize(file.size)}
                      </span>
                    </div>
                    <button
                      onClick={() => handleRemoveFile(index)}
                      className="p-1 hover:bg-gray-700 rounded transition-colors"
                    >
                      <Trash2 className="w-4 h-4 text-gray-500 hover:text-red-400" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Status Messages */}
          {uploadStatus === 'success' && (
            <div className="flex items-center gap-2 text-green-400 bg-green-900/20 rounded-lg p-3">
              <CheckCircle className="w-5 h-5" />
              <span className="text-sm">
                Successfully uploaded {uploadedFiles.length} file(s)
              </span>
            </div>
          )}

          {uploadStatus === 'error' && (
            <div className="flex items-center gap-2 text-red-400 bg-red-900/20 rounded-lg p-3">
              <AlertCircle className="w-5 h-5" />
              <span className="text-sm">{errorMessage}</span>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-4 border-t border-gray-700">
          <button
            onClick={handleClose}
            className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleUpload}
            disabled={files.length === 0 || isUploading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-lg text-sm font-medium transition-colors"
          >
            {isUploading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                Upload
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
