package tools;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.s3.AmazonS3;
import com.amazonaws.services.s3.AmazonS3ClientBuilder;
import com.amazonaws.services.s3.model.S3Object;
import com.fasterxml.jackson.annotation.JsonAutoDetect;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.PropertyAccessor;
import com.fasterxml.jackson.databind.MapperFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.json.JsonMapper;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.concurrent.RecursiveTask;
import java.util.concurrent.ForkJoinPool;
import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.HashMap;
import java.util.Arrays;
import java.util.stream.Collectors;

public class StockAnalyzerLambda
        implements RequestHandler<StockAnalyzerLambda.ToolEvent, Map<String, String>> {
    private final AmazonS3 s3Client = AmazonS3ClientBuilder.standard().build();
    private final ObjectMapper objectMapper = new ObjectMapper();
    private static final int MOVING_AVERAGE_WINDOW = 3;
    private final Map<String, ToolHandler> tools;

    public StockAnalyzerLambda() {
        tools = new HashMap<>();
        tools.put("calculate_moving_average", this::calculateMovingAverage);
        tools.put("calculate_volatility", this::calculateVolatility);
    }

    // Input/Output Classes
    public static class ToolEvent {
        @JsonProperty("id")
        private String id;

        @JsonProperty("input")
        private ToolInput input;

        @JsonProperty("name")
        private String name;

        @JsonProperty("type")
        private String type;

        public String getId() {
            return id;
        }

        public void setId(String id) {
            this.id = id;
        }

        public ToolInput getInput() {
            return input;
        }

        public void setInput(ToolInput input) {
            this.input = input;
        }

        public String getName() {
            return name;
        }

        public void setName(String name) {
            this.name = name;
        }

        public String getType() {
            return type;
        }

        public void setType(String type) {
            this.type = type;
        }
    }

    public static class ToolInput {
        @JsonProperty("bucket")
        private String bucket;

        @JsonProperty("key")
        private String key;

        public String getBucket() {
            return bucket;
        }

        public void setBucket(String bucket) {
            this.bucket = bucket;
        }

        public String getKey() {
            return key;
        }

        public void setKey(String key) {
            this.key = key;
        }
    }

    // Tool Handler Interface
    @FunctionalInterface
    interface ToolHandler {
        String execute(ToolInput input) throws Exception;
    }

    // Main Handler Method
    @Override
    public Map<String, String> handleRequest(ToolEvent event, Context context) {
        try {
            String result = "";
            switch (event.getName()) {
                case "calculate_moving_average":
                    result = calculateMovingAverage(event.getInput());
                    break;
                case "calculate_volatility":
                    result = calculateVolatility(event.getInput());
                    break;
                default:
                    result = String.format("no such tool %s", event.getName());
            }

            Map<String, String> response = new HashMap<>();
            response.put("type", "tool_result");
            response.put("tool_use_id", event.getId());
            response.put("content", result);
            
            return response;
            
        } catch (Exception e) {
            Map<String, String> errorResponse = new HashMap<>();
            errorResponse.put("type", "tool_result");
            errorResponse.put("tool_use_id", event.getId());
            errorResponse.put("content", String.format("error executing tool %s: %s", event.getName(), e.getMessage()));
            return errorResponse;
        }
    }

    // Tool Implementations
    private String calculateMovingAverage(ToolInput input) throws Exception {
        Map<String, List<Double>> stockData = readStockDataFromS3(input.getBucket(), input.getKey());

        ForkJoinPool pool = ForkJoinPool.commonPool();
        List<String> symbols = new ArrayList<>(stockData.keySet());
        MultiStockAnalysis task = new MultiStockAnalysis(stockData, symbols, 0, symbols.size(), MOVING_AVERAGE_WINDOW);

        Map<String, List<Double>> result = pool.invoke(task);
        return objectMapper.writeValueAsString(result);
    }

    private String calculateVolatility(ToolInput input) throws Exception {
        Map<String, List<Double>> stockData = readStockDataFromS3(input.getBucket(), input.getKey());
        Map<String, Double> volatilities = new HashMap<>();

        for (Map.Entry<String, List<Double>> entry : stockData.entrySet()) {
            List<Double> prices = entry.getValue();
            double volatility = calculateHistoricalVolatility(prices);
            volatilities.put(entry.getKey(), volatility);
        }

        return objectMapper.writeValueAsString(volatilities);
    }

    // Utility Methods
    protected Map<String, List<Double>> readStockDataFromS3(String bucket, String key) {
        Map<String, List<Double>> stockData = new HashMap<>();

        try (S3Object s3Object = s3Client.getObject(bucket, key);
                BufferedReader reader = new BufferedReader(new InputStreamReader(s3Object.getObjectContent()))) {

            String line;
            while ((line = reader.readLine()) != null) {
                String[] values = line.split(",");
                if (values.length > 1) {
                    String ticker = values[0];
                    List<Double> prices = Arrays.stream(values)
                            .skip(1)
                            .map(String::trim)
                            .filter(s -> !s.isEmpty())
                            .map(Double::parseDouble)
                            .collect(Collectors.toList());
                    stockData.put(ticker, prices);
                }
            }
        } catch (Exception e) {
            throw new RuntimeException("Error reading from S3: " + e.getMessage(), e);
        }

        return stockData;
    }

    protected double calculateHistoricalVolatility(List<Double> prices) {
        List<Double> returns = new ArrayList<>();
        for (int i = 1; i < prices.size(); i++) {
            returns.add(Math.log(prices.get(i) / prices.get(i - 1)));
        }

        double mean = returns.stream().mapToDouble(Double::doubleValue).average().orElse(0.0);
        double variance = returns.stream()
                .mapToDouble(r -> Math.pow(r - mean, 2))
                .average().orElse(0.0);

        return Math.sqrt(variance * 252) * 100;
    }

    // Fork/Join Framework Classes
    public static class MovingAverageTask extends RecursiveTask<List<Double>> {
        private final List<Double> prices;
        private final int start;
        private final int end;
        private final int window;
        private static final int THRESHOLD = 1000;

        public MovingAverageTask(List<Double> prices, int start, int end, int window) {
            this.prices = prices;
            this.start = start;
            this.end = end;
            this.window = window;
        }

        @Override
        protected List<Double> compute() {
            if (end - start <= THRESHOLD) {
                return computeDirectly();
            }

            int mid = start + (end - start) / 2;
            MovingAverageTask leftTask = new MovingAverageTask(prices, start, mid, window);
            MovingAverageTask rightTask = new MovingAverageTask(prices, mid, end, window);

            leftTask.fork();
            List<Double> rightResult = rightTask.compute();
            List<Double> leftResult = leftTask.join();

            leftResult.addAll(rightResult);
            return leftResult;
        }

        private List<Double> computeDirectly() {
            List<Double> result = new ArrayList<>();
            for (int i = start; i < end; i++) {
                if (i < window - 1) {
                    result.add(Double.NaN);
                    continue;
                }

                double sum = 0;
                for (int j = 0; j < window; j++) {
                    sum += prices.get(i - j);
                }
                result.add(sum / window);
            }
            return result;
        }
    }

    public static class MultiStockAnalysis extends RecursiveTask<Map<String, List<Double>>> {
        private final Map<String, List<Double>> stockData;
        private final List<String> symbols;
        private final int start;
        private final int end;
        private final int window;

        public MultiStockAnalysis(Map<String, List<Double>> stockData, List<String> symbols,
                int start, int end, int window) {
            this.stockData = stockData;
            this.symbols = symbols;
            this.start = start;
            this.end = end;
            this.window = window;
        }

        @Override
        protected Map<String, List<Double>> compute() {
            if (end - start <= 1) {
                Map<String, List<Double>> result = new HashMap<>();
                String symbol = symbols.get(start);
                result.put(symbol, calculateMovingAverage(stockData.get(symbol), window));
                return result;
            }

            int mid = start + (end - start) / 2;
            MultiStockAnalysis leftTask = new MultiStockAnalysis(stockData, symbols, start, mid, window);
            MultiStockAnalysis rightTask = new MultiStockAnalysis(stockData, symbols, mid, end, window);

            leftTask.fork();
            Map<String, List<Double>> rightResult = rightTask.compute();
            Map<String, List<Double>> leftResult = leftTask.join();

            leftResult.putAll(rightResult);
            return leftResult;
        }

        private List<Double> calculateMovingAverage(List<Double> prices, int window) {
            ForkJoinPool pool = ForkJoinPool.commonPool();
            MovingAverageTask task = new MovingAverageTask(prices, 0, prices.size(), window);
            return pool.invoke(task);
        }
    }
}