module abs_diff_i13312_o6656(a,b,r);
input [6655:0] a,b;
output [6655:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
