module mul_i240_o240 (a, b, r);
input [119:0] a,b;
output [239:0] r;

assign r = a * b;

endmodule
