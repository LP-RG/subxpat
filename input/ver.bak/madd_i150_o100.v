module madd_i150_o100 (a, b, c, r);
input [49:0] a,b,c;
output [99:0] r;

assign r = (a * b) + c;

endmodule
