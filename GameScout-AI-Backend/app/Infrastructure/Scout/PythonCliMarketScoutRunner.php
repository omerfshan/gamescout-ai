<?php
declare(strict_types=1);
namespace App\Infrastructure\Scout;
use App\Domain\Scout\MarketScoutRunner;
use Symfony\Component\Process\Process;
final class PythonCliMarketScoutRunner implements MarketScoutRunner
{
    public function run(string $provider = 'auto'): array
    {
        $repoRoot = dirname(base_path());
        $aiServicePath = $repoRoot . '/GameScout-AI-AI-Service';
        $command = ['python3', '-m', 'gamescout_ai', 'scout', '--provider', $provider];
        if (app()->environment('testing')) {
            $command[] = '--no-network';
        }
        $pathEnv = getenv('PATH');
        if (!is_string($pathEnv) || $pathEnv === '') {
            $pathEnv = (string) ($_SERVER['PATH'] ?? '/usr/local/bin:/usr/bin:/bin');
        }
        $env = [
            'PYTHONPATH' => $aiServicePath,
            'AI_PROVIDER' => (string) env('AI_PROVIDER', $provider),
            'OLLAMA_BASE_URL' => (string) env('OLLAMA_BASE_URL', 'http://127.0.0.1:11434'),
            'OLLAMA_MODEL' => (string) env('OLLAMA_MODEL', 'qwen2.5:3b'),
            'OLLAMA_MODELS' => (string) env('OLLAMA_MODELS', $repoRoot . '/.orchestra/tools/ollama/models'),
            'AI_API_KEY' => (string) env('AI_API_KEY', ''),
            'AI_BASE_URL' => (string) env('AI_BASE_URL', ''),
            'AI_MODEL' => (string) env('AI_MODEL', ''),
            'PATH' => $pathEnv,
        ];
        $process = new Process($command, $aiServicePath, $env, null, 95.0);
        $process->run();
        if (!$process->isSuccessful()) {
            throw new \RuntimeException('Pazar keşif motoru çalıştırılamadı.');
        }
        try {
            /** @var array<string, mixed> $decoded */
            $decoded = json_decode($process->getOutput(), true, 512, JSON_THROW_ON_ERROR);
            return $decoded;
        } catch (\JsonException $e) {
            throw new \RuntimeException('Pazar keşif motoru çıktısı çözümlenemedi.', 0, $e);
        }
    }
}
