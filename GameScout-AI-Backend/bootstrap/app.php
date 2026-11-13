<?php
declare(strict_types=1);
use Illuminate\Foundation\Application;
use Illuminate\Foundation\Configuration\Exceptions;
use Illuminate\Foundation\Configuration\Middleware;
use Illuminate\Auth\AuthenticationException;
use Illuminate\Validation\ValidationException;
use App\Domain\Auth\InvalidCredentials;
use App\Domain\Games\ImportConflict;
return Application::configure(basePath: dirname(__DIR__))
    ->withRouting(api: __DIR__.'/../routes/api.php', health: '/up')
    ->withMiddleware(function (Middleware $middleware): void {
        $middleware->append(\App\Http\Middleware\LimitJsonBody::class);
    })
    ->withExceptions(function (Exceptions $exceptions): void {
        $exceptions->shouldRenderJsonWhen(fn () => true);
        $exceptions->render(fn (AuthenticationException $e) => response()->json(['error'=>['code'=>'unauthenticated','message'=>'Oturum açmanız gerekiyor.']],401));
        $exceptions->render(fn (InvalidCredentials $e) => response()->json(['error'=>['code'=>'invalid_credentials','message'=>$e->getMessage()]],401));
        $exceptions->render(fn (ValidationException $e) => response()->json(['error'=>['code'=>'validation_failed','message'=>'İstek verisi geçersiz.','details'=>$e->errors()]],422));
        $exceptions->render(fn (ImportConflict $e) => response()->json(['error'=>['code'=>'import_conflict','message'=>$e->getMessage()]],409));
        $exceptions->render(function (\Throwable $e) {
            $status = $e instanceof \Symfony\Component\HttpKernel\Exception\HttpExceptionInterface ? $e->getStatusCode() : 500;
            return response()->json(['error'=>['code'=>$status===500 ? 'internal_error' : 'http_error','message'=>$status===500 ? 'İşlem tamamlanamadı.' : 'İstek işlenemedi.']],$status);
        });
    })->create();
