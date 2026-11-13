<?php
declare(strict_types=1);
namespace App\Http\Middleware;
use Closure;
use Illuminate\Http\Request;
final class LimitJsonBody
{
    public function handle(Request $request, Closure $next)
    {
        if (strlen($request->getContent())>1048576) {
            return response()->json(['error'=>['code'=>'payload_too_large','message'=>'En fazla 1 MiB JSON kabul edilir.']],413);
        }
        if ($request->isMethod('POST') && ($request->is('api/v1/imports') || $request->is('api/v1/auth/login'))) {
            if (!$request->isJson()) {
                return response()->json(['error'=>['code'=>'unsupported_media_type','message'=>'application/json gerekli.']],415);
            }
            try { json_decode($request->getContent(),true,512,JSON_THROW_ON_ERROR); }
            catch (\JsonException) { return response()->json(['error'=>['code'=>'invalid_json','message'=>'Geçersiz JSON.']],400); }
        }
        return $next($request);
    }
}
