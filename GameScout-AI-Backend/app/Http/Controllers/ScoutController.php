<?php
declare(strict_types=1);
namespace App\Http\Controllers;
use App\Application\Scout\{GetLatestScoutReport, RunMarketScout};
use App\Http\Requests\RunScoutRequest;
use Illuminate\Http\{JsonResponse, Request};
final class ScoutController
{
    public function latest(Request $request, GetLatestScoutReport $useCase): JsonResponse
    {
        $ownerId = (int) $request->user()->getAuthIdentifier();
        $meta = [
            'configured_provider' => (string) env('AI_PROVIDER', 'auto'),
            'ollama_base_url' => (string) env('OLLAMA_BASE_URL', 'http://127.0.0.1:11434'),
            'ollama_model' => (string) env('OLLAMA_MODEL', 'qwen2.5:3b'),
            'api_configured' => trim((string) env('AI_API_KEY', '')) !== '',
        ];
        return response()->json($useCase->execute($ownerId, $meta), 200);
    }
    public function run(RunScoutRequest $request, RunMarketScout $useCase): JsonResponse
    {
        $ownerId = (int) $request->user()->getAuthIdentifier();
        $provider = (string) ($request->validated('provider') ?? env('AI_PROVIDER', 'auto'));
        return response()->json($useCase->execute($ownerId, $provider), 201);
    }
}
