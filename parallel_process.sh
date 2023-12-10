python3 api_request_parallel_processor.py \
    --requests_filepath data/nyt_qa_requests_to_parallel_process.jsonl \
    --save_filepath data/nyt_qa_requests_to_parallel_process_results.jsonl \
    --max_requests_per_minute 375 \
    --max_tokens_per_minute 750000 \
    --token_encoding_name cl100k_base \
    --max_attempts 5 \
    --logging_level 20