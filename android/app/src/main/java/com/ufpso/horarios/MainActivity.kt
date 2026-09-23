package com.ufpso.horarios

import android.annotation.SuppressLint
import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.webkit.*
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout
import androidx.webkit.WebViewAssetLoader

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var swipeRefresh: SwipeRefreshLayout
    private var fileChooserCallback: ValueCallback<Array<Uri>>? = null

    // IMPORTANTE: esta IP debe coincidir con la IP LAN actual de la máquina que ejecuta ./start.sh
    // (se puede obtener con `ip -4 addr`). Si se despliega el backend en un dominio/URL pública,
    // reemplázala por esa URL (ej: "https://api.midominio.com/").
    private val liveServerUrl = "http://10.80.85.104:8000/"
    private val localFallbackUrl = "https://appassets.androidplatform.net/assets/web/index.html"
    private var isUsingFallback = false

    private val filePickerLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            val intent = result.data
            val results: Array<Uri>? = when {
                intent?.clipData != null -> {
                    val count = intent.clipData!!.itemCount
                    Array(count) { i -> intent.clipData!!.getItemAt(i).uri }
                }
                intent?.data != null -> arrayOf(intent.data!!)
                else -> null
            }
            fileChooserCallback?.onReceiveValue(results)
        } else {
            fileChooserCallback?.onReceiveValue(null)
        }
        fileChooserCallback = null
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        swipeRefresh = SwipeRefreshLayout(this).apply {
            setColorSchemeColors(android.graphics.Color.parseColor("#DC2626"))
        }

        // Configurar WebViewAssetLoader para servir assets locales bajo origen seguro HTTPS
        val assetLoader = WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(this))
            .build()

        webView = WebView(this).apply {
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.allowFileAccess = true
            settings.allowContentAccess = true
            settings.loadWithOverviewMode = true
            settings.useWideViewPort = true
            settings.databaseEnabled = true
            settings.cacheMode = WebSettings.LOAD_DEFAULT
            settings.mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW

            webViewClient = object : WebViewClient() {
                override fun shouldInterceptRequest(
                    view: WebView,
                    request: WebResourceRequest
                ): WebResourceResponse? {
                    return assetLoader.shouldInterceptRequest(request.url)
                }

                override fun onPageFinished(view: WebView?, url: String?) {
                    super.onPageFinished(view, url)
                    swipeRefresh.isRefreshing = false

                    // Al cargar el fallback empaquetado, inyectar la base de la API apuntando al
                    // mismo servidor que se intentó cargar, para que el bundle pueda consumir datos
                    // si el servidor sí es alcanzable (misma red). Si el usuario configuró una URL
                    // personalizada en el modal, se respeta (localStorage ya tiene prioridad).
                    if (isUsingFallback) {
                        webView.evaluateJavascript(
                            "if(!localStorage.getItem('ufpso_api_base')){" +
                                "localStorage.setItem('ufpso_api_base','" + liveServerUrl + "api/v1'" +
                                ");console.log('[UFPSO] api_base inyectado: " + liveServerUrl + "api/v1');}",
                            null
                        )
                    }
                }

                override fun onReceivedError(
                    view: WebView?,
                    request: WebResourceRequest?,
                    error: WebResourceError?
                ) {
                    super.onReceivedError(view, request, error)
                    swipeRefresh.isRefreshing = false

                    // Solo saltar al fallback si falla la CARGA PRINCIPAL de la página.
                    // Los errores de subrecursos (fetch a /api/v1/*, css, js, fuentes) NO deben
                    // cambiar la interfaz: un fallo transitorio de red provocaba que la app
                    // "retrocediera" a la UI vieja empaquetada, y los cambios en tiempo real
                    // parecían no aplicarse.
                    val failingUrl = request?.url?.toString() ?: ""
                    if (!isUsingFallback && request?.isForMainFrame == true && failingUrl.startsWith(liveServerUrl)) {
                        isUsingFallback = true
                        webView.loadUrl(localFallbackUrl)
                    }
                }

                // Los errores HTTP (4xx/5xx) tampoco deben disparar el fallback.
                override fun onReceivedHttpError(
                    view: WebView?,
                    request: WebResourceRequest?,
                    errorResponse: WebResourceResponse?
                ) {
                    super.onReceivedHttpError(view, request, errorResponse)
                    swipeRefresh.isRefreshing = false
                }
            }

            webChromeClient = object : WebChromeClient() {
                override fun onShowFileChooser(
                    webView: WebView?,
                    filePathCallback: ValueCallback<Array<Uri>>?,
                    fileChooserParams: FileChooserParams?
                ): Boolean {
                    fileChooserCallback?.onReceiveValue(null)
                    fileChooserCallback = filePathCallback

                    val intent = Intent(Intent.ACTION_GET_CONTENT).apply {
                        addCategory(Intent.CATEGORY_OPENABLE)
                        type = "application/pdf"
                    }
                    filePickerLauncher.launch(Intent.createChooser(intent, "Seleccionar Horario SIA (PDF)"))
                    return true
                }
            }
        }

        swipeRefresh.addView(webView)
        swipeRefresh.setOnRefreshListener {
            isUsingFallback = false
            // Limpiar caché HTTP del WebView para que el pull-to-refresh SIEMPRE traiga
            // el frontend y los datos más recientes (tiempo real).
            webView.clearCache(true)
            webView.settings.cacheMode = WebSettings.LOAD_NO_CACHE
            webView.loadUrl(liveServerUrl)
            webView.settings.cacheMode = WebSettings.LOAD_DEFAULT
        }

        setContentView(swipeRefresh)

        // Cargar preferentemente desde el servidor en vivo para que los cambios se reflejen de inmediato
        webView.loadUrl(liveServerUrl)
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }
}
