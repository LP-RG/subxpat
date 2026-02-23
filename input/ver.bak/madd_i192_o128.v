module madd_i192_o128 (a, b, c, r);
input [63:0] a,b,c;
output [127:0] r;

assign r = (a * b) + c;

endmodule
