<?php

declare(strict_types=1);

$provider = strtolower(trim((string) env('AI_PROVIDER', 'ollama')));
$provider = $provider === 'auto' ? 'ollama' : $provider;
$allowPaid = filter_var(env('SCOUT_ALLOW_PAID_PROVIDERS', false), FILTER_VALIDATE_BOOL);
$allowed = ['ollama'];
if ($allowPaid) {
    $allowed = array_merge($allowed, ['openai', 'gemini']);
}

return [
    'provider' => in_array($provider, $allowed, true) ? $provider : 'ollama',
    'allowed_providers' => $allowed,
    'allow_paid_providers' => $allowPaid,
    'ollama_base_url' => env('OLLAMA_BASE_URL', 'http://127.0.0.1:11434'),
    'ollama_model' => env('OLLAMA_MODEL', 'qwen3:8b'),
    'timeout_seconds' => 150,
];
