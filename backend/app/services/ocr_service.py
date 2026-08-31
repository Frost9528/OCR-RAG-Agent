"""
PaddleOCR Service for Document Parsing
"""

import logging
import time
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio

from app.config import settings
from app.models.schemas import ParsedBlock, OCRResult, BlockType, DocumentStats

logger = logging.getLogger(__name__)

class OCRService:
    """PaddleOCR 文档解析服务"""

    def __init__(self):
        self.pipeline = None
        self._initialized = False

    async def initialize(self):
        """初始化 OCR 服务"""
        if self._initialized:
            return

        if settings.ocr_mode == "cloud":
            logger.info("OCR mode: cloud, skipping local pipeline init")
            self._initialized = True
            return

        try:
            logger.info("Initializing PaddleOCR pipeline...")

            # 在线程池中初始化（避免阻塞）
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._init_pipeline)

            if self.pipeline is not None:
                self._initialized = True
                logger.info("PaddleOCR pipeline initialized successfully")
            else:
                raise Exception("Pipeline initialization returned None")
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            logger.warning("PaddleOCR initialization failed, service will not be available")
            self._initialized = False
            self.pipeline = None

    def _init_pipeline(self):
        """初始化 pipeline（同步）"""
        try:
            import os
            # 设置使用 GPU 1（避免与 GPU 0 上的其他服务冲突）
            os.environ['CUDA_VISIBLE_DEVICES'] = '1'

            from paddleocr import PaddleOCRVL

            self.pipeline = PaddleOCRVL(
                vl_rec_model_dir=settings.paddleocr_vl_model_dir,
                layout_detection_model_dir=settings.layout_detection_model_dir
            )
            logger.info(f"PaddleOCRVL loaded with model: {settings.paddleocr_vl_model_dir} on GPU 1")
        except Exception as e:
            logger.error(f"Error in _init_pipeline: {e}")
            self.pipeline = None
            raise

    async def parse_document(
        self,
        file_path: str,
        doc_id: str,
        output_dir: Optional[str] = None
    ) -> List[OCRResult]:
        """
        解析文档并返回结构化结果

        Args:
            file_path: 文档路径
            doc_id: 文档ID
            output_dir: 输出目录（保存JSON、Markdown等）

        Returns:
            每页的 OCR 结果列表
        """
        if not self._initialized:
            await self.initialize()

        if settings.ocr_mode == "cloud":
            return await self._parse_cloud(file_path, doc_id, output_dir)

        # 检查 pipeline 是否可用
        if self.pipeline is None:
            raise Exception("PaddleOCR pipeline is not available. Please check the initialization logs.")

        try:
            start_time = time.time()

            # 准备输出目录
            if output_dir is None:
                output_dir = Path(settings.upload_dir) / doc_id
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # 在线程池中执行 OCR（避免阻塞）
            loop = asyncio.get_event_loop()
            ocr_outputs = await loop.run_in_executor(
                None,
                self._run_ocr,
                file_path,
                str(output_dir)
            )

            # 从保存的JSON文件解析结果(而不是从内存对象)
            results = []
            json_files = sorted(output_dir.glob("*_res.json"))

            if json_files:
                # 从JSON文件读取
                import json
                for json_file in json_files:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                    ocr_result = self._parse_json_output(json_data, doc_id)
                    results.append(ocr_result)
                    logger.info(f"Parsed {json_file.name}: {len(ocr_result.blocks)} blocks")
            else:
                # Fallback: 从内存对象解析
                for res in ocr_outputs:
                    ocr_result = self._parse_ocr_output(res, doc_id)
                    results.append(ocr_result)

            processing_time = time.time() - start_time
            logger.info(
                f"Document {doc_id} parsed: {len(results)} pages, "
                f"time: {processing_time:.2f}s"
            )

            return results

        except Exception as e:
            logger.error(f"Error parsing document {doc_id}: {e}")
            raise

    def _run_ocr(self, file_path: str, output_dir: str):
        """运行 OCR（同步）"""
        output = self.pipeline.predict(
            input=file_path,
            save_path=output_dir
        )

        # 保存结果到文件
        for res in output:
            res.save_to_json(save_path=output_dir)
            res.save_to_markdown(save_path=output_dir)
            res.save_to_img(save_path=output_dir)  # 保存可视化图片

        return output

    def _parse_json_output(self, json_data: dict, doc_id: str) -> OCRResult:
        """从JSON数据解析OCR结果"""
        # 确保page_index是整数
        page_index = json_data.get('page_index')
        if page_index is None:
            page_index = 0

        parsing_results = json_data.get('parsing_res_list', [])

        # 转换为 ParsedBlock
        blocks = []
        for item in parsing_results:
            try:
                # 确保block_order是整数或None
                block_order = item.get('block_order')
                if block_order is not None and not isinstance(block_order, int):
                    try:
                        block_order = int(block_order)
                    except:
                        block_order = None

                block = ParsedBlock(
                    block_id=item.get('block_id', 0),
                    block_label=item.get('block_label', 'text'),
                    block_content=item.get('block_content', ''),
                    block_bbox=item.get('block_bbox', [0, 0, 0, 0]),
                    block_order=block_order,
                    page_index=page_index
                )
                blocks.append(block)
            except Exception as e:
                logger.warning(f"Failed to parse block: {e}")
                continue

        return OCRResult(
            doc_id=doc_id,
            page_index=page_index,
            blocks=blocks,
            total_blocks=len(blocks),
            processing_time=0.0
        )

    def _parse_ocr_output(self, res, doc_id: str) -> OCRResult:
        """解析单页 OCR 输出(从内存对象)"""
        # 获取原始数据
        page_data = res.__dict__ if hasattr(res, '__dict__') else {}

        page_index = page_data.get('page_index', 0)
        parsing_results = page_data.get('parsing_res_list', [])

        # 转换为 ParsedBlock
        blocks = []
        for item in parsing_results:
            try:
                block = ParsedBlock(
                    block_id=item.get('block_id', 0),
                    block_label=item.get('block_label', 'text'),
                    block_content=item.get('block_content', ''),
                    block_bbox=item.get('block_bbox', [0, 0, 0, 0]),
                    block_order=item.get('block_order'),
                    page_index=page_index
                )
                blocks.append(block)
            except Exception as e:
                logger.warning(f"Failed to parse block: {e}")
                continue

        return OCRResult(
            doc_id=doc_id,
            page_index=page_index,
            blocks=blocks,
            total_blocks=len(blocks),
            processing_time=0.0
        )

    def calculate_stats(self, ocr_results: List[OCRResult]) -> DocumentStats:
        """计算文档统计信息"""
        stats = DocumentStats(
            doc_id=ocr_results[0].doc_id if ocr_results else "",
            text_blocks=0,
            table_blocks=0,
            image_blocks=0,
            formula_blocks=0,
            total_blocks=0
        )

        for result in ocr_results:
            for block in result.blocks:
                stats.total_blocks += 1

                label = block.block_label.lower()
                if 'table' in label:
                    stats.table_blocks += 1
                elif any(x in label for x in ['image', 'figure', 'chart']):
                    stats.image_blocks += 1
                elif 'formula' in label or 'equation' in label:
                    stats.formula_blocks += 1
                else:
                    stats.text_blocks += 1

        return stats

    def get_block_type(self, label: str) -> str:
        """获取块类型的统一标签"""
        label = label.lower()

        if 'table' in label:
            return 'table'
        elif any(x in label for x in ['image', 'figure', 'chart']):
            return 'image'
        elif 'formula' in label or 'equation' in label:
            return 'formula'
        else:
            return 'text'

    async def _parse_cloud(self, file_path: str, doc_id: str, output_dir: Optional[str] = None) -> List[OCRResult]:
        """调用飞桨云端 OCR API，使用 prunedResult 结构化数据支持文本/表格/公式/图片"""
        import base64
        import json as _json
        import requests as req
        from pathlib import Path as P

        start_time = time.time()
        suffix = P(file_path).suffix.lower()
        file_type = 0 if suffix == ".pdf" else 1

        with open(file_path, "rb") as f:
            file_data = base64.b64encode(f.read()).decode("ascii")

        headers = {
            "Authorization": f"token {settings.paddleocr_api_token}",
            "Content-Type": "application/json"
        }
        payload = {"file": file_data, "fileType": file_type}

        logger.info(f"Calling cloud OCR API for doc {doc_id}, fileType={file_type}")
        # 对瞬时 5xx 做最多 3 次重试（指数退避）
        import time as _time
        last_exc = None
        for attempt in range(3):
            try:
                response = req.post(settings.paddleocr_api_url, json=payload, headers=headers, timeout=120)
                if response.status_code < 500:
                    break
                # 5xx：记录响应体后重试
                logger.warning(
                    f"Cloud OCR API attempt {attempt+1} returned {response.status_code}: "
                    f"{response.text[:200]}"
                )
                last_exc = Exception(f"HTTP {response.status_code}: {response.text[:200]}")
            except req.exceptions.RequestException as e:
                logger.warning(f"Cloud OCR API attempt {attempt+1} failed: {e}")
                last_exc = e
            if attempt < 2:
                _time.sleep(2 ** attempt)  # 1s, 2s
        else:
            raise last_exc or Exception("Cloud OCR API failed after 3 attempts")
        response.raise_for_status()

        # 确定保存目录
        if output_dir is None:
            save_dir = P(settings.upload_dir) / doc_id
        else:
            save_dir = P(output_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        imgs_dir = save_dir / "imgs"
        imgs_dir.mkdir(exist_ok=True)

        # label 映射：将 API 返回的标签统一为内部类型
        LABEL_MAP = {
            "display_formula": "formula",
            "paragraph_title": "text",
            "doc_title": "text",
            "header": "text",
            "figure_title": "text",
            "chart": "image",
            "figure": "image",
        }

        layout_results = response.json()["result"]["layoutParsingResults"]
        results = []

        for i, res in enumerate(layout_results):
            # 1. 下载所有图片到 imgs/
            images_map = res["markdown"].get("images", {})
            for img_rel_path, img_url in images_map.items():
                img_name = P(img_rel_path).name
                try:
                    img_bytes = req.get(img_url, timeout=30).content
                    with open(imgs_dir / img_name, "wb") as imgf:
                        imgf.write(img_bytes)
                except Exception as e:
                    logger.warning(f"Failed to download image {img_url}: {e}")

            # 2. 下载布局检测可视化图（layout_det_res 等）
            for key, url in res.get("outputImages", {}).items():
                try:
                    img_bytes = req.get(url, timeout=30).content
                    with open(save_dir / f"page_{i}_{key}.jpg", "wb") as imgf:
                        imgf.write(img_bytes)
                except Exception as e:
                    logger.warning(f"Failed to download output image {key}: {e}")

            # 3. 使用 prunedResult.parsing_res_list 获取结构化 blocks
            raw_blocks = res.get("prunedResult", {}).get("parsing_res_list", [])
            blocks = []

            for b in raw_blocks:
                raw_label = b.get("block_label", "text")
                label = LABEL_MAP.get(raw_label, raw_label)
                content = b.get("block_content") or ""
                bbox = b.get("block_bbox", [0, 0, 0, 0])

                if label == "image":
                    # 图片块 content 为空，从 raw_label + bbox 推导 API 图片路径
                    # API 保存文件名格式: img_in_{raw_label}_box_{x1}_{y1}_{x2}_{y2}.jpg
                    if len(bbox) >= 4:
                        img_name = f"img_in_{raw_label}_box_{bbox[0]}_{bbox[1]}_{bbox[2]}_{bbox[3]}.jpg"
                        content = f"/api/documents/{doc_id}/images/{img_name}"

                elif label == "table" and content:
                    # 修复表格内嵌图片路径 + API 标记引入 alt 属性双引号 bug
                    content = content.replace(
                        'src="imgs/',
                        f'src="{settings.server_base_url}/api/documents/{doc_id}/images/'
                    )
                    content = content.replace('alt="Image""', 'alt="Image"')

                blocks.append(ParsedBlock(
                    block_id=b.get("block_id", 0),
                    block_label=label,
                    block_content=content,
                    block_bbox=bbox,
                    block_order=b.get("block_order", 0),
                    page_index=i,
                ))

            # Fallback：prunedResult 为空时降级为整页 markdown 文本
            if not blocks:
                blocks = [ParsedBlock(
                    block_id=0, block_label="text",
                    block_content=res["markdown"]["text"],
                    block_bbox=[0, 0, 0, 0], block_order=0, page_index=i,
                )]

            results.append(OCRResult(
                doc_id=doc_id, page_index=i,
                blocks=blocks, total_blocks=len(blocks),
                processing_time=time.time() - start_time,
            ))

        # 4. 写入 page_{i}_res.json，供 /blocks 接口读取
        for ocr_result in results:
            page_file = save_dir / f"page_{ocr_result.page_index}_res.json"
            with open(page_file, "w", encoding="utf-8") as fj:
                _json.dump({
                    "page_index": ocr_result.page_index,
                    "parsing_res_list": [
                        {
                            "block_id": b.block_id,
                            "block_label": b.block_label,
                            "block_content": b.block_content,
                            "block_bbox": b.block_bbox,
                            "block_order": b.block_order or 0,
                        }
                        for b in ocr_result.blocks
                    ]
                }, fj, ensure_ascii=False)

        logger.info(
            f"Cloud OCR done for {doc_id}: {len(results)} pages, "
            f"{sum(len(r.blocks) for r in results)} blocks, {time.time()-start_time:.2f}s"
        )
        return results

    async def cleanup(self):
        """清理资源"""
        self.pipeline = None
        self._initialized = False
        logger.info("OCR service cleaned up")
