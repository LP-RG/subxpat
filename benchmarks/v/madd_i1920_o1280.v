module madd_i1920_o1280 (a, b, c, r);
input [639:0] a,b,c;
output [1279:0] r;

assign r = (a * b) + c;

endmodule
