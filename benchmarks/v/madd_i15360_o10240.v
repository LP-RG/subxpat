module madd_i15360_o10240 (a, b, c, r);
input [5119:0] a,b,c;
output [10239:0] r;

assign r = (a * b) + c;

endmodule
