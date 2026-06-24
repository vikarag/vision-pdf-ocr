# Remote NAS/Host Fallback Workflow

When attempting to use `vision-pdf-ocr` on a remote host (e.g., a NAS via SSH) and encountering missing dependencies or setup issues:

## The Fallback Pattern
1. **Pull Locally**: `scp` the target PDFs from the remote host to the local Hermes environment.
2. **Local Processing**: Use `execute_code` with `PyMuPDF` (`fitz`) for text-based PDFs. This is often faster than setting up the full OCR pipeline remotely if the PDFs are not scanned images.
3. **Drafting**: Perform the reasoning/drafting on the local machine where tools are stable.
4. **Push Back**: `scp` the results back to the remote host.

## Writable Directory Discovery
If the remote target path is a read-only mount (common on NAS units), use `ls -ld` to check permissions and fallback to the user's home directory (`~/`) for delivery.
