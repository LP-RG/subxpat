module abs_diff_i252_o126(a,b,r);
input [125:0] a,b;
output [125:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
