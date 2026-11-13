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
            'configured_provider' => (string) config('scout.provider', 'ollama'),
            'ollama_model' => (string) config('scout.ollama_model', 'qwen3:8b'),
            'allowed_providers' => array_values(config('scout.allowed_providers', ['ollama'])),
            'api_configured' => trim((string) env('AI_API_KEY', '')) !== '',
        ];
        return response()->json($useCase->execute($ownerId, $meta), 200);
    }
    public function run(RunScoutRequest $request, RunMarketScout $useCase): JsonResponse
    {
        $ownerId = (int) $request->user()->getAuthIdentifier();
        $provider = (string) ($request->validated('provider') ?? 'auto');
        $genre = (string) ($request->validated('genre') ?? 'all');
        return response()->json($useCase->execute($ownerId, $provider, $genre), 201);
    }
}
