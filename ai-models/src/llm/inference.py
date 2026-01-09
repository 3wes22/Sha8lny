"""
LLM inference engine
"""
import torch
from typing import Optional, List, Dict
import json
import re
import logging

logger = logging.getLogger(__name__)


class LLMInference:
    """Inference engine for LLM models"""

    def __init__(self, model, tokenizer, device: str = "auto"):
        """
        Initialize inference engine

        Args:
            model: Loaded model
            tokenizer: Loaded tokenizer
            device: Device to use
        """
        self.model = model
        self.tokenizer = tokenizer
        self.device = device

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        do_sample: bool = True,
        stop_sequences: Optional[List[str]] = None
    ) -> str:
        """
        Generate text from prompt

        Args:
            prompt: Input prompt
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            do_sample: Whether to use sampling
            stop_sequences: Optional stop sequences

        Returns:
            Generated text
        """
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048
        ).to(self.model.device)

        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=do_sample,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )

        # Decode
        generated_text = self.tokenizer.decode(
            outputs[0],
            skip_special_tokens=True
        )

        # Extract only the generated part (remove prompt)
        generated_text = generated_text[len(prompt):].strip()

        return generated_text

    def generate_json(
        self,
        prompt: str,
        max_retries: int = 3,
        **kwargs
    ) -> Dict:
        """
        Generate and parse JSON output

        Args:
            prompt: Input prompt
            max_retries: Maximum retry attempts
            **kwargs: Additional generation arguments

        Returns:
            Parsed JSON dictionary

        Raises:
            ValueError: If JSON parsing fails after retries
        """
        for attempt in range(max_retries):
            try:
                # Generate text
                output = self.generate(prompt, **kwargs)

                # Extract JSON (handle cases where model adds extra text)
                json_match = re.search(r'\{.*\}', output, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = output

                # Parse JSON
                result = json.loads(json_str)
                return result

            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    logger.error(f"Failed output: {output[:200]}...")
                    raise ValueError(f"Failed to generate valid JSON after {max_retries} attempts")
                continue

        raise ValueError("Failed to generate valid JSON after retries")
