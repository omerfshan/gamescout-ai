<?php
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\{AuthController, GameController, ScoutController};
Route::prefix('v1')->group(function (): void {
    Route::post('/auth/login', [AuthController::class, 'login']);
    Route::middleware('auth:sanctum')->group(function (): void {
        Route::get('/auth/me', [AuthController::class, 'me']);
        Route::post('/auth/logout', [AuthController::class, 'logout']);
        Route::post('/imports', [GameController::class, 'import']);
        Route::get('/games', [GameController::class, 'index']);
        Route::get('/scout/latest', [ScoutController::class, 'latest']);
        Route::post('/scout/runs', [ScoutController::class, 'run']);
    });
});
