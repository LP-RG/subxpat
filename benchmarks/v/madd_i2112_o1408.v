module madd_i2112_o1408 (a, b, c, r);
input [703:0] a,b,c;
output [1407:0] r;

assign r = (a * b) + c;

endmodule
