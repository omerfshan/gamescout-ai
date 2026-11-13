<?php
declare(strict_types=1);
namespace App\Http\Controllers;
use App\Application\Games\{ImportDemoGames,ListGames};
use App\Http\Requests\{ImportGamesRequest,ListGamesRequest};
use Illuminate\Http\JsonResponse;
final class GameController
{
    public function import(ImportGamesRequest $request, ImportDemoGames $useCase): JsonResponse
    {
        return response()->json(['data'=>$useCase->execute((int)$request->user()->getAuthIdentifier(),$request->validated('games'))],201);
    }
    public function index(ListGamesRequest $request, ListGames $useCase): JsonResponse
    {
        return response()->json($useCase->execute((int)$request->user()->getAuthIdentifier(),$request->validated('platform')));
    }
}
