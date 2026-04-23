module mul_i480_o480 (a, b, r);
input [239:0] a,b;
output [479:0] r;

assign r = a * b;

endmodule
