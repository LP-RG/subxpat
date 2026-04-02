module madd_i360_o240 (a, b, c, r);
input [119:0] a,b,c;
output [239:0] r;

assign r = (a * b) + c;

endmodule
