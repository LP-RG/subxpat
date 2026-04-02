module madd_i69_o46 (a, b, c, r);
input [22:0] a,b,c;
output [45:0] r;

assign r = (a * b) + c;

endmodule
