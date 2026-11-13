<?php
declare(strict_types=1);
namespace App\Infrastructure\Scout;
use App\Domain\Scout\MarketScoutRunner;
use Symfony\Component\Process\Process;
final class PythonCliMarketScoutRunner implements MarketScoutRunner
{
    public function run(string $provider = 'ollama', string $genre = 'all'): array
    {
        // This first adapter remains synchronous; a durable job worker is a separate slice.
        $repoRoot = dirname(base_path());
        $aiServicePath = $repoRoot . '/GameScout-AI-AI-Service';
        $command = ['python3', '-m', 'gamescout_ai', 'scout', '--provider', $provider, '--genre', $genre];
        if (app()->environment('testing')) {
            $command[] = '--no-network';
        }
        $pathEnv = getenv('PATH');
        if (!is_string($pathEnv) || $pathEnv === '') {
            $pathEnv = (string) ($_SERVER['PATH'] ?? '/usr/local/bin:/usr/bin:/bin');
        }
        $env = [
            'PYTHONPATH' => $aiServicePath,
            'AI_PROVIDER' => $provider,
            'OLLAMA_BASE_URL' => (string) config('scout.ollama_base_url', 'http://127.0.0.1:11434'),
            'OLLAMA_MODEL' => (string) config('scout.ollama_model', 'qwen3:8b'),
            'OLLAMA_MODELS' => (string) env('OLLAMA_MODELS', $repoRoot . '/.orchestra/tools/ollama/models'),
            'AI_API_KEY' => (string) env('AI_API_KEY', ''),
            'AI_BASE_URL' => (string) env('AI_BASE_URL', ''),
            'AI_MODEL' => (string) env('AI_MODEL', ''),
            'PATH' => $pathEnv,
            'GAMESCOUT_DISABLE_OLLAMA_AUTOSTART' => '1',
        ];
        $timeout = max(10, min(180, (int) config('scout.timeout_seconds', 150)));
        $process = new Process($command, $aiServicePath, $env, null, $timeout);
        $process->run();
        if (!$process->isSuccessful()) {
            throw new \RuntimeException('Pazar keşif motoru çalıştırılamadı.');
        }
        try {
            $output = $process->getOutput();
            if (strlen($output) > 2 * 1024 * 1024) {
                throw new \RuntimeException('Pazar keşif motoru çıktısı boyut sınırını aştı.');
            }
            $decoded = json_decode($output, true, 512, JSON_THROW_ON_ERROR);
            if (!is_array($decoded) || array_is_list($decoded)) {
                throw new \RuntimeException('Pazar keşif motoru rapor nesnesi döndürmedi.');
            }
            return $decoded;
        } catch (\JsonException $e) {
            throw new \RuntimeException('Pazar keşif motoru çıktısı çözümlenemedi.', 0, $e);
        }
    }
}
