<?php
declare(strict_types=1);
namespace App\Http\Controllers;
use App\Application\Auth\{GetAuthenticatedUser, LoginUser, LogoutUser};
use App\Domain\Auth\AuthenticatedUser;
use App\Http\Requests\LoginRequest;
use Illuminate\Http\{JsonResponse, Request};
final class AuthController
{
    public function login(LoginRequest $request, LoginUser $useCase): JsonResponse
    {
        $session = $useCase->execute(
            (string) $request->validated('email'),
            (string) $request->validated('password'),
            (string) ($request->validated('device_name') ?? 'dashboard')
        );
        return response()->json(['data' => $session], 200);
    }
    public function me(Request $request, GetAuthenticatedUser $useCase): JsonResponse
    {
        $user = $request->user();
        $domainUser = new AuthenticatedUser(
            (int) $user->getAuthIdentifier(),
            (string) $user->name,
            (string) $user->email
        );
        return response()->json(['data' => $useCase->execute($domainUser)], 200);
    }
    public function logout(Request $request, LogoutUser $useCase): JsonResponse
    {
        $user = $request->user();
        $token = $user?->currentAccessToken();
        $tokenId = is_object($token) && isset($token->id) && is_numeric($token->id) ? (int) $token->id : null;
        $useCase->execute((int) $user->getAuthIdentifier(), $tokenId);
        return response()->json(['data' => ['logged_out' => true]], 200);
    }
}
